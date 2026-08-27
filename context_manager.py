"""
context_manager.py — Gayatri AI v5.0
Markdown-driven context & guardrail system (Section 5). Scans /workspace/*.md,
chunks each file by reusing search_engine.split_sections, ranks chunks per-query
via search_engine.hybrid_score, and assembles the final system message in a
fixed priority order. system_rules.md is always injected in full.
"""

import os
import glob
from dataclasses import dataclass, field

import config
import db
from search_engine import split_sections, hybrid_score, normalize_ws
from memory_manager import MemoryManager


@dataclass
class MDChunk:
    source_id: str          # filename, e.g. "project_context.md"
    text: str
    index: int               # position of this chunk within its source file
    score: float = 0.0       # relevance score, populated per-query
    scope: str = "global"    # "global" (/workspace) or "session" (Section 5A) — internal only, never shown in the UI


@dataclass
class MDFile:
    filename: str
    path: str
    raw_text: str
    chunks: list[MDChunk] = field(default_factory=list)
    enabled: bool = True      # toggled from Context Center UI


class ContextManager:
    def __init__(self, workspace_dir: str = None):
        self.workspace_dir = workspace_dir or config.WORKSPACE_DIR
        self.files: dict[str, MDFile] = {}   # filename -> MDFile
        self.memory_manager = MemoryManager()
        self.load_all()

    # ------------------------------------------------------------------
    # Loading & chunking
    # ------------------------------------------------------------------
    def load_all(self) -> None:
        """Scan /workspace/*.md, read each, chunk via split_sections. Call on
        app start and on 'Refresh Context' action."""
        self.files = {}
        os.makedirs(self.workspace_dir, exist_ok=True)

        md_paths = sorted(glob.glob(os.path.join(self.workspace_dir, "*.md")))
        for path in md_paths:
            filename = os.path.basename(path)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    raw_text = f.read()
            except OSError:
                continue

            sections = split_sections(raw_text)
            chunks = [
                MDChunk(source_id=filename, text=chunk, index=i)
                for i, chunk in enumerate(sections)
            ]

            # task_memory.md is always active and hidden from toggles;
            # everything else defaults ON per Section 5.3.
            default_enabled = True

            self.files[filename] = MDFile(
                filename=filename,
                path=path,
                raw_text=raw_text,
                chunks=chunks,
                enabled=default_enabled,
            )

    def list_files(self) -> list[str]:
        """Filenames detected in /workspace, sorted. Used to populate Context
        Center toggle rows (excluding task_memory.md and system_rules.md, which are hidden/always active)."""
        return [
            fn for fn in sorted(self.files.keys())
            if fn not in (config.TASK_MEMORY_FILE, config.SYSTEM_RULES_FILE)
        ]

    def set_enabled(self, filename: str, enabled: bool) -> None:
        if filename == config.TASK_MEMORY_FILE:
            return  # always active, cannot be toggled off
        if filename in self.files:
            self.files[filename].enabled = enabled

    def add_context_file(self, source_path: str) -> str:
        """Copies a new .md file into /workspace and loads it. Returns the
        new filename. Used by the 'Add Context File' UI button."""
        filename = os.path.basename(source_path)
        dest_path = os.path.join(self.workspace_dir, filename)

        with open(source_path, "r", encoding="utf-8") as src:
            content = src.read()
        with open(dest_path, "w", encoding="utf-8") as dst:
            dst.write(content)

        self.load_all()
        return filename

    def write_task_memory(self, content: str) -> None:
        """Overwrites task_memory.md with session-scoped notes. Auto-managed,
        not user-edited per Section 5.1."""
        path = os.path.join(self.workspace_dir, config.TASK_MEMORY_FILE)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        self.load_all()

    # ------------------------------------------------------------------
    # Section 5A: Per-session context files (thread-scoped, stored in DB)
    # ------------------------------------------------------------------
    def get_session_chunks(self, session_id: int) -> list[MDChunk]:
        """Loads this thread's own enabled .md files from the DB and chunks
        them via the same split_sections() logic used for global files.
        Returns an empty list if session_id is None or has no files."""
        if session_id is None:
            return []

        chunks: list[MDChunk] = []
        for f in db.get_session_context_files(session_id):
            if not f["enabled"]:
                continue
            sections = split_sections(f["content"])
            for i, chunk_text in enumerate(sections):
                chunks.append(MDChunk(source_id=f["filename"], text=chunk_text, index=i, scope="session"))
        return chunks

    def list_session_files(self, session_id: int) -> list[dict]:
        """Raw file rows (id, filename, enabled, ...) for a session — used to
        populate the 'This Chat's Files' sidebar toggle rows (Section 5A.4)."""
        if session_id is None:
            return []
        return db.get_session_context_files(session_id)

    # ------------------------------------------------------------------
    # Rough token estimate (chars/4 heuristic — no extra tokenizer dependency)
    # ------------------------------------------------------------------
    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return max(1, len(text) // 4)

    # ------------------------------------------------------------------
    # Per-query ranking + assembly
    # ------------------------------------------------------------------
    def get_relevant_chunks(self, query: str, session_id: int = None) -> tuple[str, list[MDChunk]]:
        """
        Returns (system_rules_full_text, ranked_chunks) where ranked_chunks
        are the top-N (MAX_MD_CHUNKS) chunks across all enabled non-system-rules
        global files AND this thread's own enabled session files (Section 5A),
        ranked together, respecting MAX_MD_TOKENS budget. system_rules.md
        content is returned separately since it's always included in full,
        never ranked or trimmed.
        """
        system_rules_text = ""
        if config.SYSTEM_RULES_FILE in self.files:
            system_rules_text = self.files[config.SYSTEM_RULES_FILE].raw_text.strip()

        # task_memory.md is always active; include alongside other enabled files
        candidate_chunks: list[MDChunk] = []
        for filename, md_file in self.files.items():
            if filename == config.SYSTEM_RULES_FILE:
                continue
            is_task_memory = filename == config.TASK_MEMORY_FILE
            if not md_file.enabled and not is_task_memory:
                continue
            candidate_chunks.extend(md_file.chunks)

        # Section 5A: this thread's own per-session files, ranked alongside globals
        candidate_chunks.extend(self.get_session_chunks(session_id))

        if not candidate_chunks:
            return system_rules_text, []

        texts = [c.text for c in candidate_chunks]
        scores = hybrid_score(texts, query)
        for chunk, score in zip(candidate_chunks, scores):
            chunk.score = score

        ranked = sorted(candidate_chunks, key=lambda c: c.score, reverse=True)

        selected: list[MDChunk] = []
        token_budget = config.MAX_MD_TOKENS
        for chunk in ranked:
            if len(selected) >= config.MAX_MD_CHUNKS:
                break
            chunk_tokens = self._estimate_tokens(chunk.text)
            if chunk_tokens > token_budget and selected:
                # keep going only if we still have room in budget for smaller chunks
                continue
            if chunk_tokens > token_budget and not selected:
                # single oversized chunk with nothing selected yet: include it anyway
                # (better than injecting nothing) but stop after.
                selected.append(chunk)
                break
            selected.append(chunk)
            token_budget -= chunk_tokens

        return system_rules_text, selected

    def build_system_context(self, query: str, history_summary: str = "",
                              session_id: int = None) -> tuple[str, list[str]]:
        """
        Assembles the markdown portion of the system message in the fixed
        priority order (Section 5.2, amended by 5A):
          1. Full system_rules.md (never omitted)
          2. Top-ranked relevant chunks from global files AND this thread's
             own session files, ranked together (source distinguished only
             internally — the UI's two toggle sections already separate them)
          3. (web excerpts are appended later, by search_engine.build_grounded_messages)
          4. Recent conversation history summary (older turns only — recent
             turns are now passed as real messages, see Section 5A.3)

        Returns (assembled_text, chunks_used_labels) — chunks_used_labels is
        for the UI's "chunks used" transparency badge (Section 5.3), and shows
        plain filenames regardless of global/session scope.
        """
        system_rules_text, ranked_chunks = self.get_relevant_chunks(query, session_id=session_id)

        parts = []
        chunks_used_labels = []

        if system_rules_text:
            parts.append(f"# HARD GUARDRAILS ({config.SYSTEM_RULES_FILE})\n{system_rules_text}")
            chunks_used_labels.append(f"{config.SYSTEM_RULES_FILE} (full)")

        if ranked_chunks:
            grouped: dict[str, list[str]] = {}
            for chunk in ranked_chunks:
                grouped.setdefault(chunk.source_id, []).append(chunk.text)
                chunks_used_labels.append(f"{chunk.source_id} #{chunk.index}")

            context_blocks = []
            for source_id, texts in grouped.items():
                joined = "\n".join(f"- {normalize_ws(t)}" for t in texts)
                context_blocks.append(f"## {source_id}\n{joined}")

            parts.append("# PROJECT CONTEXT\n" + "\n\n".join(context_blocks))

        # Long-Term Memory (Second Brain) injection
        memories = self.memory_manager.retrieve_relevant_memories(query)
        if memories:
            memory_context = self.memory_manager.format_memory_context(memories)
            if memory_context:
                parts.append(memory_context)
                chunks_used_labels.append(f"{len(memories)} memories")

        if history_summary.strip():
            parts.append(f"# RECENT CONVERSATION HISTORY\n{history_summary.strip()}")

        assembled = "\n\n---\n\n".join(parts)
        return assembled, chunks_used_labels


def summarize_history(turns: list[dict], max_turns: int = None) -> str:
    """
    Builds a plain-text summary of the last N conversation turns for injection
    as system context (Section 5.2, step 4). `turns` is a list of
    {"role": "user"|"assistant", "content": str} dicts in chronological order.
    """
    limit = max_turns if max_turns is not None else config.HISTORY_TURNS
    recent = turns[-limit:] if limit > 0 else []
    if not recent:
        return ""

    lines = []
    for turn in recent:
        role = turn.get("role", "user").capitalize()
        content = normalize_ws(turn.get("content", ""))
        if len(content) > 300:
            content = content[:300] + "..."
        lines.append(f"{role}: {content}")

    return "\n".join(lines)