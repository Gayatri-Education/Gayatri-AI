"""
config.py — Gayatri AI v5.0
Single source of truth for all constants, paths, and tunable parameters.
Nothing in this project should hardcode a URL, port, model name, path, or
theme value outside of this file.
"""

import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.join(BASE_DIR, "workspace")
DB_PATH = os.path.join(BASE_DIR, "gayatri.db")
EXPORT_DIR = os.path.join(BASE_DIR, "exports")

# Ensure required directories exist at import time (no crash on fresh clone)
os.makedirs(WORKSPACE_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# LM Studio (OpenAI-compatible local server) — replaces legacy Ollama config
# ---------------------------------------------------------------------------
LMSTUDIO_BASE_URL = "http://127.0.0.1:1234/v1"   # editable from UI settings panel
LMSTUDIO_MODELS_ENDPOINT = "/models"
LMSTUDIO_CHAT_ENDPOINT = "/chat/completions"

DEFAULT_MODEL = ""          # populated at runtime from GET /models; no hardcoded model id
HTTP_TIMEOUT = 30           # seconds, general HTTP timeout (page fetch, LM Studio calls)
LLM_TIMEOUT = (15.0, 300.0)  # (connect, read) timeout in seconds; allows ample time for VRAM loading
STREAM_TEMP = 0.1           # temperature for streaming chat completions
GATE_TEMP = 0.0             # temperature for search-gate / keyword JSON calls (deterministic)
MAX_TOKENS_CHAT = 512       # max_tokens for main chat completion
MAX_TOKENS_GATE = 200       # max_tokens for search-gate / keyword generation calls

# ---------------------------------------------------------------------------
# Search Engine — ported from legacy gayatri_ai.py, behavior preserved
# ---------------------------------------------------------------------------
FETCH_CONCURRENCY = 6                # threaded fetch pool size for crawl_site
MAX_BYTES = 1_500_000                # truncate_bytes ceiling per fetched page
MAX_INTERNAL_LINKS = 8               # cap on same-domain links followed by gather_internal
SEARCH_RESULTS_PER_QUERY = 6         # DuckDuckGo results requested per keyword query
MAX_SOURCES = 6                      # cap on deduped sources after multi_search_enhanced
MAX_CTX_TOKENS = 3000                # token budget for assembled web-excerpt context

SECTION_MIN = 400                    # split_sections: minimum chunk size (chars)
SECTION_MAX = 1200                   # split_sections: maximum chunk size (chars)
MAX_SECTIONS = 40                    # split_sections: hard cap on sections per document

# Hybrid relevance scoring weights (must sum to 1.0)
SEMANTIC_WEIGHT = 0.55
TFIDF_WEIGHT = 0.45
EMBED_MODEL = "all-MiniLM-L6-v2"     # sentence-transformers model for sim_sem

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 GayatriAI/5.0"
)

# Search-gate cache (TTLCache) settings
GATE_CACHE_MAXSIZE = 256
GATE_CACHE_TTL_SECONDS = 900         # 15 minutes
GATE_CONFIDENCE_THRESHOLD = 0.85     # below this, fall back from heuristic to LLM gate

# choose_length adaptive word-count targets by query type
LENGTH_BRIEF = 80
LENGTH_COMPARE = 350
LENGTH_VERIFY = 200
LENGTH_DEFAULT = 250

# ---------------------------------------------------------------------------
# Markdown-Driven Context & Guardrail System (Section 5)
# ---------------------------------------------------------------------------
MAX_MD_CHUNKS = 6            # top-N ranked chunks injected per query (excl. system_rules.md)
MAX_MD_TOKENS = 1200         # token budget for injected markdown context
HISTORY_TURNS = 6            # number of recent conversation turns summarized into system prompt

SYSTEM_RULES_FILE = "system_rules.md"        # always injected in full, never trimmed
TASK_MEMORY_FILE = "task_memory.md"          # always active, hidden from UI toggles
DEFAULT_CONTEXT_FILES = [
    "system_rules.md",
    "project_context.md",
    "brand_voice.md",
    "response_contract.md",
]

# ---------------------------------------------------------------------------
# Session / Stats defaults
# ---------------------------------------------------------------------------
DEFAULT_SESSION_TITLE = "New Chat"

# ---------------------------------------------------------------------------
# Search mode toggle values (Top bar / Section 6.2)
# ---------------------------------------------------------------------------
SEARCH_MODE_AUTO = "auto"
SEARCH_MODE_FORCE_WEB = "force_web"
SEARCH_MODE_FORCE_NONE = "force_none"
SEARCH_MODE_URL_ONLY = "url_only"
SEARCH_MODE_DEEP_RESEARCH = "deep_research"
DEFAULT_SEARCH_MODE = SEARCH_MODE_AUTO

# ---------------------------------------------------------------------------
# Deep Research Mode Parameters
# ---------------------------------------------------------------------------
MAX_RESEARCH_HOPS = 2                # Maximum iterative search loops
MAX_SUB_QUERIES = 3                  # Max sub-questions decomposed per hop
MAX_SOURCES_DEEP = 12                # Max total sources collected during deep research
DEEP_RESEARCH_MAX_TOKENS = 3000      # Max output tokens for research dossier

# ---------------------------------------------------------------------------
# Persistent Long-Term Memory (Second Brain) Parameters
# ---------------------------------------------------------------------------
ENABLE_LONG_TERM_MEMORY = True
MAX_MEMORY_ITEMS_IN_PROMPT = 6       # Maximum relevant memories injected per turn
MEMORY_CONFIDENCE_THRESHOLD = 0.65   # Minimum extraction confidence score (0.0 - 1.0)

# ---------------------------------------------------------------------------
# Terracotta & Indigo Slate Theme (Flet UI)
# ---------------------------------------------------------------------------
THEME_DARK = {
    "bg": "#1A1A1A",                  # --background
    "surface": "#202020",             # --card / --popover
    "surface_sidebar": "#1F1F1F",     # --sidebar
    "surface_input": "#303030",       # --input
    "surface_muted": "#2A2A2A",       # --muted
    "border": "#353535",              # --border / --sidebar-border
    "accent_primary": "#DF6035",      # --primary (Terracotta)
    "accent_secondary": "#284167",    # --secondary (Deep Indigo)
    "accent_highlight": "#EF4444",    # --destructive
    "accent_subtle": "#2A3656",       # --accent
    "accent_subtle_text": "#BFDBFE",  # --accent-foreground
    "accent_green": "#E16F41",        # --chart-2
    "chart_1": "#85A6C7",             # --chart-1
    "text_primary": "#E5E5E5",        # --foreground / --card-foreground
    "text_secondary": "#808080",      # --muted-foreground
}

THEME_LIGHT = {
    "bg": "#E8EBED",                  # --background
    "surface": "#FFFFFF",             # --card / --popover
    "surface_sidebar": "#DDDFE2",     # --sidebar
    "surface_input": "#F4F5F7",       # --input
    "surface_muted": "#F9FAFB",       # --muted
    "border": "#CCCCCC",              # --border
    "border_sidebar": "#E5E7EB",      # --sidebar-border
    "accent_primary": "#DF6035",      # --primary (Terracotta)
    "accent_secondary": "#2F4B79",    # --secondary (Deep Slate Indigo)
    "accent_highlight": "#EF4444",    # --destructive
    "accent_subtle": "#D6E4F0",       # --accent
    "accent_subtle_text": "#1E3A8A",  # --accent-foreground
    "accent_green": "#7399BF",        # --chart-1
    "chart_1": "#7399BF",
    "text_primary": "#333333",        # --foreground / --card-foreground
    "text_secondary": "#6B7280",      # --muted-foreground
}

FONT_FAMILY = "Outfit, sans-serif"
FONT_MONO = "Fira Code, monospace"
BORDER_RADIUS = 12                   # ~0.5rem - 0.75rem
SIDEBAR_WIDTH = 280                  # px, per layout spec

# ---------------------------------------------------------------------------
# Feature toggles
# ---------------------------------------------------------------------------
ENABLE_AUTOSAVE = True
ENABLE_STREAMING = True
ENABLE_URL_DIRECT_CRAWL = True