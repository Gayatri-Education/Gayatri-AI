"""
search_engine.py — Gayatri AI v5.0
Ported from legacy gayatri_ai.py. Behavior preserved: search gating,
keyword generation, TF-IDF + SBERT hybrid scoring, page cleaning/chunking,
crawling. Only the LLM backend changed (Ollama -> LM Studio via llm_client.py).
"""

import re
import time
import threading
import concurrent.futures
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from readability import Document
import tldextract
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from ddgs import DDGS

import config
from llm_client import LLMClient, LMStudioError

# ---------------------------------------------------------------------------
# Lazy-loaded embedding model (expensive to init; shared singleton)
# ---------------------------------------------------------------------------
_embed_model_lock = threading.Lock()
_embed_model = None


def _get_embed_model():
    global _embed_model
    if _embed_model is None:
        with _embed_model_lock:
            if _embed_model is None:
                from sentence_transformers import SentenceTransformer
                _embed_model = SentenceTransformer(config.EMBED_MODEL)
    return _embed_model


# ---------------------------------------------------------------------------
# TTL Cache — used for the search-gate cache
# ---------------------------------------------------------------------------
class TTLCache:
    def __init__(self, maxsize: int = 256, ttl: int = 900):
        self.maxsize = maxsize
        self.ttl = ttl
        self._store: dict[str, tuple[float, object]] = {}
        self._lock = threading.Lock()

    def get(self, key: str):
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return None
            ts, value = item
            if time.time() - ts > self.ttl:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value):
        with self._lock:
            if len(self._store) >= self.maxsize and key not in self._store:
                oldest_key = min(self._store, key=lambda k: self._store[k][0])
                del self._store[oldest_key]
            self._store[key] = (time.time(), value)


GATE_CACHE = TTLCache(maxsize=config.GATE_CACHE_MAXSIZE, ttl=config.GATE_CACHE_TTL_SECONDS)


# ---------------------------------------------------------------------------
# Utility layer
# ---------------------------------------------------------------------------
def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


URL_RE = re.compile(r"https?://[^\s<>\"')\]]+")


def extract_urls(text: str) -> list[str]:
    return URL_RE.findall(text or "")


def is_binary(content_type: str) -> bool:
    if not content_type:
        return False
    ct = content_type.lower()
    text_like = ("text/", "application/json", "application/xml", "application/xhtml")
    return not any(ct.startswith(p) for p in text_like)


def truncate_bytes(data: bytes, max_bytes: int = None) -> bytes:
    limit = max_bytes if max_bytes is not None else config.MAX_BYTES
    return data[:limit]


def same_domain(url_a: str, url_b: str) -> bool:
    a = tldextract.extract(url_a)
    b = tldextract.extract(url_b)
    return (a.domain, a.suffix) == (b.domain, b.suffix)


def http_get(url: str, timeout: int = None) -> requests.Response | None:
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": config.UA},
            timeout=timeout if timeout is not None else config.HTTP_TIMEOUT,
        )
        if resp.status_code != 200:
            return None
        if is_binary(resp.headers.get("Content-Type", "")):
            return None
        return resp
    except requests.RequestException:
        return None


# ---------------------------------------------------------------------------
# HTML cleaning + chunking
# ---------------------------------------------------------------------------
def clean_html(html: str) -> str:
    """Extract main readable content. readability first, BeautifulSoup fallback."""
    try:
        doc = Document(html)
        summary_html = doc.summary()
        soup = BeautifulSoup(summary_html, "html.parser")
        text = normalize_ws(soup.get_text(" "))
        if len(text) > 200:
            return text
    except Exception:
        pass

    try:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()
        return normalize_ws(soup.get_text(" "))
    except Exception:
        return ""


def split_sections(text: str, section_min: int = None, section_max: int = None,
                    max_sections: int = None) -> list[str]:
    """Chunk cleaned text into sections bounded by SECTION_MIN/MAX, capped at MAX_SECTIONS."""
    smin = section_min if section_min is not None else config.SECTION_MIN
    smax = section_max if section_max is not None else config.SECTION_MAX
    cap = max_sections if max_sections is not None else config.MAX_SECTIONS

    text = normalize_ws(text)
    if not text:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", text)
    sections = []
    current = ""

    for sent in sentences:
        candidate = (current + " " + sent).strip() if current else sent
        if len(candidate) >= smax and current:
            sections.append(current.strip())
            current = sent
        else:
            current = candidate
        if len(current) >= smax:
            sections.append(current.strip())
            current = ""

    if current and len(current) >= smin:
        sections.append(current.strip())
    elif current and sections:
        sections[-1] = (sections[-1] + " " + current).strip()
    elif current:
        sections.append(current.strip())

    return sections[:cap]


# ---------------------------------------------------------------------------
# Hybrid scoring: TF-IDF + SBERT semantic similarity
# ---------------------------------------------------------------------------
def sim_tfidf(chunks: list[str], query: str) -> list[float]:
    if not chunks:
        return []
    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform(chunks + [query])
        query_vec = matrix[-1]
        chunk_vecs = matrix[:-1]
        sims = cosine_similarity(chunk_vecs, query_vec).flatten()
        return sims.tolist()
    except ValueError:
        return [0.0] * len(chunks)


_CHUNK_EMBED_CACHE: dict[str, object] = {}
_CHUNK_EMBED_LOCK = threading.Lock()


def get_chunk_embedding(text: str, model):
    with _CHUNK_EMBED_LOCK:
        if text in _CHUNK_EMBED_CACHE:
            return _CHUNK_EMBED_CACHE[text]
    emb = model.encode([text], convert_to_numpy=True, normalize_embeddings=True)[0]
    with _CHUNK_EMBED_LOCK:
        if len(_CHUNK_EMBED_CACHE) < 2000:
            _CHUNK_EMBED_CACHE[text] = emb
    return emb


def sim_sem(chunks: list[str], query: str) -> list[float]:
    if not chunks:
        return []
    import numpy as np
    model = _get_embed_model()
    chunk_embs = np.array([get_chunk_embedding(c, model) for c in chunks])
    query_emb = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    sims = cosine_similarity(chunk_embs, query_emb).flatten()
    return sims.tolist()


def hybrid_score(chunks: list[str], query: str) -> list[float]:
    """0.55 semantic + 0.45 TF-IDF weighting, per Section 4 spec."""
    if not chunks:
        return []
    tfidf_scores = sim_tfidf(chunks, query)
    sem_scores = sim_sem(chunks, query)
    return [
        config.SEMANTIC_WEIGHT * s + config.TFIDF_WEIGHT * t
        for s, t in zip(sem_scores, tfidf_scores)
    ]


# ---------------------------------------------------------------------------
# PageDoc + fetching / crawling
# ---------------------------------------------------------------------------
@dataclass
class PageDoc:
    url: str
    title: str = ""
    text: str = ""
    sections: list[str] = field(default_factory=list)
    fetched_ok: bool = False


def fetch_doc(url: str) -> PageDoc:
    resp = http_get(url)
    if resp is None:
        return PageDoc(url=url, fetched_ok=False)

    raw = truncate_bytes(resp.content)
    html = raw.decode(resp.encoding or "utf-8", errors="ignore")

    title = ""
    try:
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        if title_match:
            title = normalize_ws(BeautifulSoup(title_match.group(1), "html.parser").get_text())
    except Exception:
        pass

    text = clean_html(html)
    sections = split_sections(text)

    return PageDoc(url=url, title=title, text=text, sections=sections, fetched_ok=bool(text))


def gather_internal(base_url: str, html: str, max_links: int = None) -> list[str]:
    cap = max_links if max_links is not None else config.MAX_INTERNAL_LINKS
    soup = BeautifulSoup(html, "html.parser")
    links = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        parsed = urlparse(href)
        if parsed.scheme not in ("http", "https"):
            continue
        href = href.split("#")[0]
        if href in seen or href == base_url:
            continue
        if not same_domain(base_url, href):
            continue
        seen.add(href)
        links.append(href)
        if len(links) >= cap:
            break

    return links


def crawl_site(start_url: str, max_pages: int = None) -> list[PageDoc]:
    """Crawl start_url plus same-domain internal links, threaded fetch."""
    cap = max_pages if max_pages is not None else config.MAX_INTERNAL_LINKS + 1

    docs: list[PageDoc] = []
    root_resp = http_get(start_url)
    if root_resp is None:
        return docs

    root_html = root_resp.text
    root_doc = fetch_doc(start_url)
    docs.append(root_doc)

    internal_links = gather_internal(start_url, root_html)
    internal_links = internal_links[: max(0, cap - 1)]

    if internal_links:
        with concurrent.futures.ThreadPoolExecutor(max_workers=config.FETCH_CONCURRENCY) as pool:
            futures = {pool.submit(fetch_doc, url): url for url in internal_links}
            for future in concurrent.futures.as_completed(futures):
                try:
                    doc = future.result()
                    if doc.fetched_ok:
                        docs.append(doc)
                except Exception:
                    continue

    return docs


# ---------------------------------------------------------------------------
# Search decision gate: heuristic fast path + LLM fallback
# ---------------------------------------------------------------------------
_TIME_SENSITIVE_PATTERNS = re.compile(
    r"\b(today|yesterday|this week|this month|this year|latest|current|currently|now|breaking|"
    r"recent|recently|update|updated|202[4-9]|price|stock|score|weather|"
    r"news|release date|who is the current|as of|who won|election|standing|schedule|market|live)\b",
    re.IGNORECASE,
)
_VERIFY_PATTERNS = re.compile(
    r"\b(verify|confirm|is it true|fact.?check|source|citation|according to|who is|where is|when was|when did)\b",
    re.IGNORECASE,
)
_STATIC_PATTERNS = re.compile(
    r"\b(explain|definition|define|what is|what are|how to|how do|how does|why is|why does|"
    r"write|code|debug|fix|create|generate|summarize|translate|convert|calculate|solve|"
    r"joke|poem|story|help me|teach me|implement|class|function|script|example|difference between|compare|pros and cons)\b",
    re.IGNORECASE,
)
_CONVERSATIONAL_PATTERNS = re.compile(
    r"^(hi|hello|hey|greetings|good morning|good afternoon|good evening|who are you|what can you do|thanks|thank you|ok|okay|bye|help)\b",
    re.IGNORECASE,
)


def heuristic_gate(query: str) -> tuple[bool, float, str, str]:
    """Fast keyword/pattern-based decision. Returns (decision, confidence, reason, category)."""
    urls = extract_urls(query)
    if urls:
        return True, 1.0, "Query contains a URL", "url"

    q_strip = query.strip()
    if _CONVERSATIONAL_PATTERNS.match(q_strip):
        return False, 0.95, "Conversational pattern detected", "static"

    if _TIME_SENSITIVE_PATTERNS.search(query):
        return True, 0.95, "Time-sensitive or current-events pattern detected", "time_sensitive"

    if _VERIFY_PATTERNS.search(query):
        return True, 0.90, "Verification/fact-check pattern detected", "verify"

    if _STATIC_PATTERNS.search(query) and not _TIME_SENSITIVE_PATTERNS.search(query):
        return False, 0.92, "Static/explanatory query pattern detected", "static"

    # Default heuristic for general reasoning & general queries
    words = q_strip.split()
    if len(words) >= 4 and not _TIME_SENSITIVE_PATTERNS.search(query):
        return False, 0.86, "General knowledge / reasoning pattern", "static"

    return False, 0.5, "No strong heuristic signal", "unclear"


_GATE_SYSTEM_PROMPT = (
    "You are a search-necessity classifier. Given a user query, decide if answering it "
    "correctly requires a live web search (e.g. current events, prices, scores, recent "
    "releases, verification of facts) versus something answerable from general knowledge "
    "(e.g. explanations, definitions, creative writing, math, translation). "
    "Respond with STRICT JSON only, no markdown, no prose, in this exact shape: "
    '{"decision": "YES", "confidence": 0.9, "reason": "short reason", "category": "time_sensitive"} '
    'The "decision" field must be "YES" or "NO". "category" must be one of: '
    '"time_sensitive", "verify", "static", "url", "unclear".'
)


def llm_gate_enhanced(query: str, client: LLMClient, model: str) -> tuple[bool, float, str, str]:
    """LLM fallback gate, used when heuristic confidence < GATE_CONFIDENCE_THRESHOLD."""
    cache_key = f"gate::{model}::{query.strip().lower()}"
    cached = GATE_CACHE.get(cache_key)
    if cached is not None:
        return cached

    messages = [
        {"role": "system", "content": _GATE_SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]

    try:
        result = client.chat_json(model, messages, temperature=config.GATE_TEMP,
                                   max_tokens=config.MAX_TOKENS_GATE)
        decision = str(result.get("decision", "NO")).strip().upper() == "YES"
        confidence = float(result.get("confidence", 0.6))
        reason = str(result.get("reason", "LLM gate decision"))
        category = str(result.get("category", "unclear"))
        parsed = (decision, confidence, reason, category)
    except (LMStudioError, ValueError, TypeError):
        # graceful degradation: default to no-search rather than crashing
        parsed = (False, 0.5, "LLM gate unavailable, defaulted to no-search", "unclear")

    GATE_CACHE.set(cache_key, parsed)
    return parsed


def needs_search(query: str, client: LLMClient, model: str) -> tuple[bool, float, str, str]:
    """Combined gate: heuristic fast path, LLM fallback when uncertain."""
    decision, confidence, reason, category = heuristic_gate(query)
    if confidence >= config.GATE_CONFIDENCE_THRESHOLD:
        return decision, confidence, reason, category
    return llm_gate_enhanced(query, client, model)


# ---------------------------------------------------------------------------
# Keyword generation
# ---------------------------------------------------------------------------
_KEYWORD_SYSTEM_PROMPT = (
    "You generate search-engine keyword queries for a user question. "
    "Produce 3 to 5 short, diverse keyword phrases (not full sentences) that would "
    "find the most relevant, authoritative, up-to-date web results. "
    "Respond with STRICT JSON only, no markdown, no prose, in this exact shape: "
    '{"keywords": ["keyword phrase 1", "keyword phrase 2", "keyword phrase 3"]}'
)


def extract_fast_keywords(query: str) -> list[str]:
    """Fast rule-based keyword extraction without calling LLM."""
    clean = re.sub(r"[^\w\s-]", " ", query)
    clean = normalize_ws(clean)
    if not clean:
        return [query.strip()]

    # Strip conversational lead-ins
    cleaned = re.sub(
        r"^(please\s+)?(can you\s+)?(tell me\s+)?(what is\s+|what are\s+|how to\s+|who is\s+|when did\s+|where is\s+|search for\s+|find\s+)",
        "", clean, flags=re.IGNORECASE
    ).strip()

    keywords = []
    if cleaned and len(cleaned) > 2:
        keywords.append(cleaned)
    if clean != cleaned and clean:
        keywords.append(clean)
    return keywords or [clean]


def gen_keywords_enhanced(query: str, client: LLMClient = None, model: str = None) -> list[str]:
    # Fast path: direct extraction avoids 3-8s local LLM latency
    fast_kw = extract_fast_keywords(query)
    if fast_kw and len(fast_kw[0].split()) <= 10:
        return fast_kw[:3]

    if client and model:
        messages = [
            {"role": "system", "content": _KEYWORD_SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ]
        try:
            result = client.chat_json(model, messages, temperature=config.GATE_TEMP,
                                       max_tokens=config.MAX_TOKENS_GATE)
            keywords = result.get("keywords", [])
            keywords = [normalize_ws(str(k)) for k in keywords if normalize_ws(str(k))]
            if keywords:
                return keywords[:5]
        except (LMStudioError, ValueError, TypeError):
            pass

    return fast_kw or [query.strip()]


# ---------------------------------------------------------------------------
# DuckDuckGo search
# ---------------------------------------------------------------------------
def duck_search(query: str, max_results: int = None) -> list[dict]:
    cap = max_results if max_results is not None else config.SEARCH_RESULTS_PER_QUERY
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=cap):
                results.append({
                    "title": r.get("title", ""),
                    "href": r.get("href", ""),
                    "body": r.get("body", ""),
                })
    except Exception:
        return []
    return results


def multi_search_enhanced(keywords: list[str], max_sources: int = None, stop_checker=None) -> list[dict]:
    """Search across multiple keyword variants in parallel, dedupe by domain, cap at MAX_SOURCES."""
    cap = max_sources if max_sources is not None else config.MAX_SOURCES
    seen_domains = set()
    sources = []

    if not keywords:
        return []

    # Parallelize web searches across up to 3 keywords
    kw_to_search = keywords[:3]
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(3, len(kw_to_search))) as pool:
        future_map = {pool.submit(duck_search, kw): kw for kw in kw_to_search}
        for future in concurrent.futures.as_completed(future_map):
            if stop_checker and stop_checker():
                break
            try:
                results = future.result()
                for r in results:
                    href = r.get("href", "")
                    if not href:
                        continue
                    ext = tldextract.extract(href)
                    domain_key = f"{ext.domain}.{ext.suffix}"
                    if domain_key in seen_domains:
                        continue
                    seen_domains.add(domain_key)
                    sources.append(r)
                    if len(sources) >= cap:
                        return sources
            except Exception:
                continue

    return sources


# ---------------------------------------------------------------------------
# Adaptive response length
# ---------------------------------------------------------------------------
def choose_length(query: str, category: str = "unclear") -> int:
    q = query.lower()
    if category == "verify" or "verify" in q or "confirm" in q or "true" in q:
        return config.LENGTH_VERIFY
    if "compare" in q or "vs" in q or "versus" in q or "difference between" in q:
        return config.LENGTH_COMPARE
    if len(q.split()) <= 6:
        return config.LENGTH_BRIEF
    return config.LENGTH_DEFAULT


# ---------------------------------------------------------------------------
# Grounded message builder — OpenAI-style messages array
# ---------------------------------------------------------------------------
def build_grounded_messages(query: str, system_context: str, sources: list[dict] = None,
                             page_docs: list[PageDoc] = None,
                             target_words: int = None,
                             conversation_turns: list[dict] = None) -> list[dict]:
    """
    Returns an OpenAI-style messages array:
    [{"role": "system", ...}, ...conversation_turns..., {"role": "user", ...}].

    `system_context` is the already-assembled guardrail + markdown context block
    from context_manager.py (Section 5). Web excerpts (from `sources` and/or
    `page_docs`) are appended after it, per the fixed priority order in Section 5.2.

    `conversation_turns` (Section 5A.3): the most recent HISTORY_TURNS real
    {"role": "user"/"assistant", "content": ...} messages from this session,
    inserted as actual message-array entries so the model has direct access
    to prior turns rather than only a paraphrased summary. Anything older than
    this window should already be compressed into `system_context` via
    context_manager.summarize_history() before calling this function — that
    summary and these real turns are complementary, not duplicates.
    """
    words = target_words if target_words is not None else config.LENGTH_DEFAULT
    system_parts = [system_context.strip()] if system_context else []

    excerpt_blocks = []
    if sources:
        for i, src in enumerate(sources, 1):
            title = src.get("title", "Untitled")
            href = src.get("href", "")
            body = normalize_ws(src.get("body", ""))[:500]
            excerpt_blocks.append(f"[Source {i}] {title} ({href})\n{body}")

    if page_docs:
        offset = len(excerpt_blocks)
        for i, doc in enumerate(page_docs, offset + 1):
            if not doc.fetched_ok:
                continue
            excerpt = " ".join(doc.sections[:3])[:800]
            excerpt_blocks.append(f"[Source {i}] {doc.title or doc.url} ({doc.url})\n{excerpt}")

    if excerpt_blocks:
        system_parts.append(
            "WEB SOURCES (cite as [Source N] where relevant):\n\n" + "\n\n".join(excerpt_blocks)
        )

    system_parts.append(
        f"Answer in approximately {words} words unless the question requires more precision."
    )
    system_parts.append(
        "Formatting: the display renders standard Markdown only, with no LaTeX/math-mode support. "
        "For chemical formulas, equations, or units, use plain Unicode subscript/superscript characters "
        "(e.g., H\u2082O, CO\u2082, C\u2086H\u2081\u2082O\u2086, x\u00b2) instead of LaTeX syntax like $H_2O$ or \\(x^2\\)."
    )

    system_message = "\n\n---\n\n".join(system_parts)

    messages = [{"role": "system", "content": system_message}]

    if conversation_turns:
        for turn in conversation_turns:
            role = turn.get("role", "user")
            if role not in ("user", "assistant"):
                continue
            content = str(turn.get("content", "")).strip()
            if content:
                messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": query})
    return messages