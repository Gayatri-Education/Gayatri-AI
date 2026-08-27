# 🤖 Gayatri AI

> A powerful, privacy-first desktop AI assistant built with [Flet](https://flet.dev/) and powered by local LLMs via [LM Studio](https://lmstudio.ai/).

---

## 🎓 Built Under the DBert Internship Program

This project was developed as part of the **[DBert Internship Program](https://dbert.online/)** — a hands-on initiative designed to equip students and developers with real-world AI and software development skills.

> 💡 Want to build real-world AI projects like this one? **[Join the DBert Internship Program →](https://dbert.online/)**

[![DBert Internship Program](https://img.shields.io/badge/DBert-Internship%20Program-blue?style=for-the-badge)](https://dbert.online/)

---

## ✨ Features

- 🧠 **Local LLM Integration** — Connects to [LM Studio](https://lmstudio.ai/) for fully offline, privacy-first AI conversations
- 🔬 **Autonomous Deep Research Mode** — Multi-hop inquiry with iterative query decomposition, evidence gap analysis, and auto-export to markdown dossiers
- 🧬 **Persistent Long-Term Memory (Second Brain)** — Background user trait/preference learning and dedicated Memory Vault with semantic context injection
- 🌐 **Web Search Grounding** — Automatically searches the web to give up-to-date, source-backed answers
- 🔗 **URL Crawling** — Paste a URL and Gayatri AI reads the entire website to answer questions about it
- 📄 **Context Files (RAG)** — Attach Markdown files as long-term or per-session context documents
- 💬 **Multi-Session Chat History** — Persistent chat sessions stored in a local SQLite database
- 🎨 **Dark / Light Theme** — Smooth animated theme switching with Terracotta & Indigo Slate design system
- 📱 **Responsive Layout** — Auto-adapts sidebar and padding to any window size
- ⚡ **Live Streaming Responses** — Real-time token streaming with step-by-step progress indicators
- 🔍 **Smart Search Modes** — Auto, Deep Research 🔬, Force Web, URL Only, or Search Off
- 📊 **Session Statistics** — Tracks keywords generated, searches performed, and sources found

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| UI Framework | [Flet](https://flet.dev/) (Flutter-powered Python UI) |
| LLM Backend | [LM Studio](https://lmstudio.ai/) (OpenAI-compatible API) |
| Default Model | Qwen 2.5 7B |
| Database | SQLite (via `db.py`) |
| Web Search | DuckDuckGo / multi-source search engine |
| Context / RAG | Custom embedding + chunk ranking (`context_manager.py`) |
| Deep Research | Multi-hop planner & gap analyzer (`deep_research.py`) |
| Second Brain | Long-term memory extraction & retrieval (`memory_manager.py`) |
| Language | Python 3.10+ |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- [LM Studio](https://lmstudio.ai/) installed and running with a local model loaded

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Gayatri-Education/Gayatri-AI.git
cd Gayatri-AI

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python main.py
```

> ⚠️ Make sure LM Studio is running on `http://localhost:1234` (default) before launching.

---

## 📁 Project Structure

```
Gayatri-AI/
├── main.py              # App entrypoint — wires all modules together
├── config.py            # App-wide configuration and theme definitions
├── ui_components.py     # All Flet UI widgets and components
├── llm_client.py        # LM Studio API client with streaming support
├── search_engine.py     # Web search, URL crawling, and grounded context builder
├── deep_research.py     # Multi-hop inquiry, gap analysis, and dossier synthesizer
├── memory_manager.py    # Long-term memory extractor & semantic retrieval engine
├── context_manager.py   # RAG context file manager with embedding + ranking
├── db.py                # SQLite database layer for sessions, messages, and memories
├── diagnostic_test.py   # Connectivity and system diagnostics
├── requirements.txt     # Python dependencies
├── exports/             # Exported research dossiers and chat transcripts
└── gayatri.db           # Local SQLite database (auto-created on first run)
```

---

## ⚙️ Configuration

Key settings live in `config.py` and can also be changed via the in-app Settings dialog:

| Setting | Default | Description |
|---|---|---|
| `LM_STUDIO_BASE_URL` | `http://localhost:1234` | LM Studio server URL |
| `DEFAULT_MODEL` | `qwen2.5-7b` | Default LLM model ID |
| `SEARCH_RESULTS_PER_QUERY` | `6` | Number of web results per search |
| `MAX_MD_TOKENS` | `1200` | Max context token budget |
| `MAX_RESEARCH_HOPS` | `2` | Max multi-hop research exploration loops |
| `ENABLE_LONG_TERM_MEMORY`| `True` | Persistent memory & Second Brain active |
| `SIDEBAR_WIDTH` | `280` | Sidebar width in pixels |

---

## 🔍 Search Modes

| Mode | Behavior |
|---|---|
| **Auto** | AI decides whether a web search is needed |
| **Deep Research 🔬** | Multi-hop autonomous inquiry, gap analysis & comprehensive dossier synthesis |
| **Web Search** | Always searches the web before responding |
| **URL Only** | Only crawls URLs pasted in the query |
| **Search Off** | Pure local LLM — no internet access |

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
| 🖥️ LM Studio | [https://lmstudio.ai/](https://lmstudio.ai/) |
| ⚡ Flet Framework | [https://flet.dev/](https://flet.dev/) |

---

<div align="center">

**Developed with ❤️ under the [DBert Internship Program](https://dbert.online/)**

[![DBert](https://img.shields.io/badge/DBert-Internship%20Program-blue?style=for-the-badge)](https://dbert.online/)

</div>
