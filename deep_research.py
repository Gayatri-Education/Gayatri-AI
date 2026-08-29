"""
deep_research.py — Gayatri AI v5.0
Autonomous Deep Research Mode (Multi-Hop Inquiry) Engine.
Performs iterative query decomposition, multi-hop web querying & crawling,
evidence gap analysis, structured dossier synthesis, and auto-export.
"""

import os
import re
import json
import time
from datetime import datetime, timezone
from typing import Callable, List, Dict, Tuple, Any

import config
from llm_client import LLMClient, LMStudioError
from search_engine import (
    multi_search_enhanced,
    crawl_site,
    split_sections,
    hybrid_score,
    extract_urls,
    normalize_ws,
)


DECOMPOSE_PROMPT = """You are Gayatri AI's Research Planning Engine.
Your task is to decompose a complex research question into {max_sub_queries} distinct, highly specific search queries that together cover the complete scope of the topic.

Ensure the sub-queries cover:
1. Core mechanisms, facts, and specifications
2. Comparative analysis, benchmarks, or alternative viewpoints
3. Real-world implementations, current updates, or limitations

User Question: {query}

Respond strictly with a valid JSON object matching this schema:
{{
  "sub_queries": [
    "search query 1",
    "search query 2"
  ]
}}
"""

GAP_ANALYSIS_PROMPT = """You are Gayatri AI's Evidence Gap Evaluator.
Review the user's original question and the research findings gathered so far.
Determine if there are critical missing angles, unaddressed questions, or specific data points that require one targeted follow-up search query.

Original Question: {query}
Gathered Findings Summary:
{summary}

Respond strictly with a valid JSON object matching this schema:
{{
  "needs_followup": true,
  "followup_query": "specific search query to fill the gap",
  "reason": "short explanation of the missing information"
}}
If the gathered evidence is already comprehensive, set "needs_followup" to false and "followup_query" to "".
"""

DEEP_RESEARCH_SYSTEM_PROMPT = """You are Gayatri AI, an elite autonomous research intelligence.
You produce rigorous, comprehensive, highly analytical, and factually grounded research dossiers.

Format your output in clean, structured GitHub Flavored Markdown adhering to this structure:
# 🔬 Deep Research Dossier: [Topic Title]

## 📌 Executive Summary
A high-level synthesis of key findings, actionable takeaways, and strategic conclusions.

## 📊 Comparative Analysis & Key Metrics
Use markdown tables wherever comparison across models, technologies, metrics, or frameworks is relevant.

## 🔍 In-Depth Analytical Breakdown
Thorough, well-reasoned sections with technical depth, architectural considerations, and concrete details.

## ⚖️ Conflicting Viewpoints, Nuances & Limitations
Any trade-offs, potential drawbacks, or conflicting data between sources.

## 📚 Evidence & Source Citations
Numbered list referencing the source documents provided.
"""


def decompose_query(query: str, llm_client: LLMClient, model: str) -> List[str]:
    """Decomposes a query into multiple focused sub-questions."""
    prompt = DECOMPOSE_PROMPT.format(max_sub_queries=config.MAX_SUB_QUERIES, query=query)
    messages = [
        {"role": "system", "content": "You are a research query planning specialist. Output JSON only."},
        {"role": "user", "content": prompt},
    ]

    try:
        data = llm_client.chat_json(model=model, messages=messages, temperature=config.GATE_TEMP)
        sub_queries = data.get("sub_queries", [])
        if isinstance(sub_queries, list) and sub_queries:
            return [str(q).strip() for q in sub_queries if str(q).strip()][:config.MAX_SUB_QUERIES]
    except Exception:
        pass

    # Fallback if LLM decomposition fails
    return [query]


def evaluate_evidence_gaps(
    query: str,
    sources: List[Dict[str, Any]],
    llm_client: LLMClient,
    model: str,
) -> Tuple[bool, str]:
    """Evaluates whether the gathered sources have gaps and suggests a refinement query."""
    if not sources:
        return True, query

    summary_snippets = []
    for i, s in enumerate(sources[:6], 1):
        title = s.get("title", "Untitled")
        body = s.get("body", "")[:250]
        summary_snippets.append(f"[{i}] {title}: {body}")

    summary_text = "\n".join(summary_snippets)
    prompt = GAP_ANALYSIS_PROMPT.format(query=query, summary=summary_text)
    messages = [
        {"role": "system", "content": "You are an evidence gap analysis engine. Output JSON only."},
        {"role": "user", "content": prompt},
    ]

    try:
        data = llm_client.chat_json(model=model, messages=messages, temperature=config.GATE_TEMP)
        needs_followup = bool(data.get("needs_followup", False))
        followup_query = str(data.get("followup_query", "")).strip()
        return needs_followup, followup_query
    except Exception:
        return False, ""


def export_research_report(query: str, report_content: str, sources: List[Dict[str, Any]]) -> str:
    """Saves the research dossier to the exports/ directory with metadata."""
    os.makedirs(config.EXPORT_DIR, exist_ok=True)
    slug = re.sub(r"[^a-zA-Z0-9_\-]+", "_", query.strip())[:30].strip("_")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"deep_research_{slug}_{timestamp}.md"
    file_path = os.path.join(config.EXPORT_DIR, filename)

    metadata_header = [
        "---",
        f"title: Deep Research — {query}",
        f"date: {datetime.now(timezone.utc).isoformat()}",
        f"sources_count: {len(sources)}",
        "engine: Gayatri AI Deep Research v5.0",
        "---",
        "",
    ]

    full_text = "\n".join(metadata_header) + report_content
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    return file_path


DEEP_RESEARCH_CONVERSATIONAL_SYSTEM_PROMPT = """You are Gayatri AI in Deep Research Mode 🔬.
The user sent a greeting or casual chat query.
Greet the user warmly in a modern, professional tone.
Explain clearly that in Deep Research Mode, you perform iterative multi-hop web search, deep page crawling, gap analysis, and generate comprehensive research dossiers with source citations.
Give 3 exciting research topic suggestions they can explore.
"""


_CONVERSATIONAL_RESEARCH_PATTERN = re.compile(
    r"^(hi|hello|hey|greetings|good (?:morning|afternoon|evening)|who are you|what can you do|how are you|thanks|thank you|ok|okay|bye|help|test|ping|howdy)\b",
    re.IGNORECASE,
)


def execute_deep_research(
    query: str,
    llm_client: LLMClient,
    model: str,
    system_context: str = "",
    step_callback: Callable[[str, str], None] = None,
    stop_checker: Callable[[], bool] = None,
) -> Tuple[str, List[Dict[str, Any]], List[str], Any]:
    """
    Autonomous multi-hop deep research workflow:
    1. Query Decomposition
    2. Hop 1: Multi-vector search & crawling
    3. Gap Analysis
    4. Hop 2: Refinement query search
    5. Evidence aggregation & Reranking
    6. Dossier synthesis & Auto-export
    """
    def log_step(text: str, status: str):
        if step_callback:
            step_callback(text, status)

    def is_stopped() -> bool:
        return bool(stop_checker and stop_checker())

    if is_stopped():
        return "⏹️ Research cancelled.", [], [], ""

    q_strip = query.strip()
    if _CONVERSATIONAL_RESEARCH_PATTERN.match(q_strip) or len(q_strip.split()) <= 2 and q_strip.lower() in {"hi", "hello", "hey", "test", "ping"}:
        messages = [
            {"role": "system", "content": f"{DEEP_RESEARCH_CONVERSATIONAL_SYSTEM_PROMPT}\n\n{system_context}".strip()},
            {"role": "user", "content": query},
        ]
        return "", [], [], messages

    all_sources: List[Dict[str, Any]] = []
    page_docs: List[str] = []
    seen_urls = set()

    # Step 1: Decompose query into research angles
    log_step("🔬 Decomposing research query into vectors...", "running")
    sub_queries = decompose_query(query, llm_client, model)
    log_step(f"🔬 Decomposed into {len(sub_queries)} research vectors", "done")

    if is_stopped():
        return "⏹️ Research cancelled.", [], [], ""

    # Step 2: Hop 1 — Parallel Multi-Vector Search
    for i, sq in enumerate(sub_queries, 1):
        if is_stopped():
            return "⏹️ Research cancelled.", all_sources, [], ""

        log_step(f"Hop 1 [{i}/{len(sub_queries)}]: Searching '{sq[:40]}...'...", "running")
        hop_sources = multi_search_enhanced([sq], stop_checker=stop_checker)
        new_sources = []
        for s in hop_sources:
            href = s.get("href", "")
            if href and href not in seen_urls:
                seen_urls.add(href)
                new_sources.append(s)

        all_sources.extend(new_sources)
        log_step(f"Hop 1 [{i}/{len(sub_queries)}]: Found {len(new_sources)} new sources", "done")

    # Direct URL crawling if URLs are explicitly present
    direct_urls = extract_urls(query)
    for url in direct_urls:
        if url not in seen_urls:
            seen_urls.add(url)
            log_step(f"Crawling referenced URL: {url[:45]}...", "running")
            chunks = crawl_site(url)
            page_docs.extend(chunks)
            log_step(f"Crawled referenced URL: {len(chunks)} chunks indexed", "done")

    if is_stopped():
        return "⏹️ Research cancelled.", all_sources, page_docs, ""

    # Step 3: Gap Analysis & Hop 2 Refinement
    log_step("Analyzing research evidence gaps...", "running")
    needs_followup, followup_query = evaluate_evidence_gaps(query, all_sources, llm_client, model)
    log_step("Analyzing research evidence gaps...", "done")

    if needs_followup and followup_query and not is_stopped():
        log_step(f"Hop 2 Refinement: Searching '{followup_query[:40]}...'...", "running")
        refinement_sources = multi_search_enhanced([followup_query], stop_checker=stop_checker)
        new_refinements = []
        for s in refinement_sources:
            href = s.get("href", "")
            if href and href not in seen_urls:
                seen_urls.add(href)
                new_refinements.append(s)
        all_sources.extend(new_refinements)
        log_step(f"Hop 2 Refinement: Added {len(new_refinements)} precision sources", "done")

    # Limit total sources
    all_sources = all_sources[:config.MAX_SOURCES_DEEP]
    log_step(f"Aggregated {len(all_sources)} verified research sources", "done")

    if is_stopped():
        return "⏹️ Research cancelled.", all_sources, page_docs, ""

    # Step 4: Prepare Grounded Synthesis Context
    log_step("Synthesizing comprehensive research dossier...", "running")

    context_snippets = []
    for i, s in enumerate(all_sources, 1):
        title = s.get("title", "Untitled")
        href = s.get("href", "")
        body = s.get("body", "")
        context_snippets.append(f"### [Source {i}] {title}\nURL: {href}\n{body}")

    for i, doc_chunk in enumerate(page_docs[:10], 1):
        context_snippets.append(f"### [Crawled Document {i}]\n{doc_chunk}")

    assembled_evidence = "\n\n".join(context_snippets)

    messages = [
        {"role": "system", "content": f"{DEEP_RESEARCH_SYSTEM_PROMPT}\n\n{system_context}".strip()},
        {
            "role": "user",
            "content": (
                f"Research Question: {query}\n\n"
                f"=== RESEARCH EVIDENCE & SOURCE EXTRACTS ===\n{assembled_evidence}\n\n"
                f"Generate the comprehensive, multi-section Deep Research Dossier now."
            ),
        },
    ]

    return "", all_sources, page_docs, messages
