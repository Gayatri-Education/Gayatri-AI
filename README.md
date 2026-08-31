# 🤖 Gayatri AI

> A powerful, privacy-first desktop AI assistant 

---

## 🎓 Built Under the DBert Internship Program

This project was developed as part of the **[DBert Internship Program](https://dbert.online/)** — a hands-on initiative designed to equip students and developers with real-world AI and software development skills.

> 💡 Want to build real-world AI projects like this one? **[Join the DBert Internship Program →](https://dbert.online/)**

[![DBert Internship Program](https://img.shields.io/badge/DBert-Internship%20Program-blue?style=for-the-badge)](https://dbert.online/)

---

## ✨ Features

- 🤖 **Autonomous Agent Mode** — Break down complex, high-level goals into multi-step action plans, dispatch specialized tools (`web_search`, `read_context`, `memory_lookup`, `reason`), track progress live, and persist task states in SQLite
- 🔬 **Autonomous Deep Research Mode** — Multi-hop inquiry with iterative query decomposition, evidence gap analysis, source verification, and auto-export to structured Markdown dossiers
- 🧬 **Persistent Long-Term Memory (Second Brain)** — Background extraction of user preferences, constraints, and facts with confidence scoring and an interactive Memory Vault UI modal
- 🧠 **Local LLM Integration** —  100% offline, privacy-first AI conversations with dynamic model discovery and streaming
- 🌐 **Web Search Grounding** — Live search with hybrid relevance scoring (Semantic Embeddings via `all-MiniLM-L6-v2` + TF-IDF)
- 🔗 **URL Crawling & Deep Scrape** — Concurrently crawls and extracts content from pasted URLs and internal links
- 📄 **Markdown-Driven RAG & Context Files** — Workspace-based context system (`workspace/`) with guardrail documents (`system_rules.md`, `project_context.md`, `brand_voice.md`)
- 💬 **Multi-Session Chat History** — Persistent chat sessions stored in a local SQLite database with renaming, search, and deletion
- 📱 **Responsive Desktop Layout** — Collapsible sidebar, stats dock, and adaptive padding for any screen resolution
- ⚡ **Live Streaming Responses** — Real-time token streaming with multi-tier fallback resilience and step-by-step execution indicators
- 🔍 **6 Intelligent Modes** — Auto, Agent Mode 🤖, Deep Research 🔬, Web Search, URL Only, or Search Off
- 📊 **Session Statistics & Diagnostics** — Tracks query keywords, searches performed, and sources discovered; includes built-in connectivity diagnostic suite

---

## 🛠️ Tech Stack

| Layer | Technology | Description |
|---|---|---|
| Agent Engine | `agent.py` | Multi-step task planner, tool dispatcher & SQLite execution tracker |
| Deep Research | `deep_research.py` | Multi-hop search planner, gap analyzer & dossier synthesizer |
| Second Brain | `memory_manager.py` | Background memory extractor & semantic retrieval engine |
| Context / RAG | `context_manager.py` | Sentence-Transformers (`all-MiniLM-L6-v2`) + TF-IDF chunk ranking |
| Web Search & Scraping | `search_engine.py` | DuckDuckGo search + multi-threaded concurrent web crawler |
| Database Layer | `db.py` | Local SQLite database for sessions, messages, memories, and agent tasks |
| Language | Python 3.10+ | Clean, modular asynchronous architecture |

---

## 🚀 Getting Started

### Prerequisites

-## Installation

```bash
# 1. Clone the repository
git clone https://github.com/Gayatri-Education/Gayatri-AI.git
cd Gayatri-AI

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python main.py
```

> 💡 **Windows Quick Start:** You can also launch Gayatri AI by double-clicking `run_gayatri_ai.bat`.


## 📁 Project Structure

```
Gayatri-AI/
├── main.py              # App entrypoint — UI orchestration and event routing
├── agent.py             # Autonomous Agent Mode (goal decomposition & tool dispatching)
├── config.py            # App-wide configuration, search parameters, and theme tokens
├── ui_components.py     # Reusable Flet widgets, Memory Vault modal, and theme styling
├── llm_client.py        # LM Studio API client with streaming and fallback support
├── search_engine.py     # Web search, URL crawler, and hybrid relevance ranker
├── deep_research.py     # Multi-hop inquiry, gap analysis, and dossier synthesizer
├── memory_manager.py    # Long-term memory extraction & semantic retrieval engine
├── context_manager.py   # Workspace RAG file manager with embedding + ranking
├── db.py                # SQLite database layer for sessions, memories, and agent tasks
├── diagnostic_test.py   # Connectivity and search diagnostic suite
├── run_gayatri_ai.bat   # Windows batch launcher script
├── requirements.txt     # Python package dependencies
├── workspace/           # Markdown context files & active system guardrails
├── exports/             # Exported research dossiers and chat transcripts
└── gayatri.db           # Local SQLite database (auto-created on first run)
```

---

## ⚙️ Configuration

Key settings live in `config.py` and can also be adjusted via the in-app Settings dialog:

| Setting | Default | Description |
|---|---|---|
| `DEFAULT_MODEL` | Auto-detected | Default LLM model ID (discovered from `/v1/models`) |
| `AGENT_MAX_STEPS` | `6` | Maximum steps in an autonomous agent execution plan |
| `AGENT_MAX_TOKENS` | `2500` | Max output token budget for agent result synthesis |
| `MAX_RESEARCH_HOPS` | `2` | Max multi-hop research exploration loops |
| `MAX_SUB_QUERIES` | `3` | Max sub-questions decomposed per research hop |
| `ENABLE_LONG_TERM_MEMORY` | `True` | Persistent memory & Second Brain active |
| `MAX_MEMORY_ITEMS_IN_PROMPT` | `6` | Maximum relevant memories injected per conversation turn |
| `SEARCH_RESULTS_PER_QUERY` | `6` | Number of web results per DuckDuckGo search |
| `MAX_MD_TOKENS` | `1200` | Max context token budget for workspace RAG files |
| `SIDEBAR_WIDTH` | `280` | Collapsible sidebar width in pixels |

---

## 🔍 Modes & Execution Strategies

| Mode | Badge | Description |
|---|---|---|
| **Auto** | `Auto` | AI automatically decides whether web search or context retrieval is needed |
| **Agent Mode** | `Agent 🤖` | Full autonomous execution: plans multi-step strategy, runs tools (`web_search`, `read_context`, `memory_lookup`, `reason`), and streams comprehensive solutions |
| **Deep Research** | `Deep Research 🔬` | Multi-hop autonomous inquiry: recursively analyzes evidence gaps, gathers cross-source data, and synthesizes structured research dossiers |
| **Web Search** | `Web Search` | Forces search and source synthesis on every query |
| **URL Only** | `URL Only` | Directly crawls and summarizes specific URLs provided in your prompt |
| **Search Off** | `Search Off` | Pure offline local LLM generation with zero internet access |

---

## 🤝 Contributing

Contributions are welcome! This project is actively developed under the [DBert Internship Program](https://dbert.online/). If you're a DBert intern or alumni:

1. Fork the [repository](https://github.com/Gayatri-Education/Gayatri-AI)
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push and open a Pull Request

---

## 📄 License

This project is open-source and developed for educational purposes under the **[DBert Internship Program](https://dbert.online/)**.

---

## 🔗 Links

| | |
|---|---|
| 🌐 DBert Internship Program | [https://dbert.online/](https://dbert.online/) |
| 📦 Repository | [https://github.com/Gayatri-Education/Gayatri-AI](https://github.com/Gayatri-Education/Gayatri-AI) |
|
---

<div align="center">

**Developed with ❤️ under the [DBert Internship Program](https://dbert.online/)**

[![DBert](https://img.shields.io/badge/DBert-Internship%20Program-blue?style=for-the-badge)](https://dbert.online/)

</div>
