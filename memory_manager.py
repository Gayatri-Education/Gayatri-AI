"""
memory_manager.py — Gayatri AI v5.0
Persistent Long-Term Memory & Evolving "Second Brain" Engine.
Automatically extracts user preferences, ongoing projects, skills, facts, and habits
from conversations in the background and injects relevant memories into context.
"""

import threading
import json
from typing import List, Dict, Any

import config
import db
from llm_client import LLMClient, LMStudioError


MEMORY_EXTRACTION_SYSTEM_PROMPT = """You are Gayatri AI's memory extraction module.
Your job is to analyze the conversation turn and identify any durable, long-term facts, preferences, project details, tech stacks, or user traits worth remembering for future chats.

DO NOT extract:
- Ephemeral/temporary questions (e.g. "What time is it in Tokyo?", "Explain binary search")
- General knowledge or transient conversational pleasantries

DO extract:
- User traits, role, background (e.g. "User is a full-stack engineer specializing in Flutter and Python")
- Personal preferences (e.g. "Prefers concise code examples with TypeScript", "Likes dark theme")
- Ongoing projects and tools (e.g. "Building Gayatri AI desktop assistant with Flet and SQLite")
- Hardware or environment details (e.g. "Runs Windows 11 with RTX 3060 local LM Studio setup")

Respond strictly with a valid JSON object matching this schema:
{
  "memories": [
    {
      "key": "short_unique_slug_identifier",
      "category": "preference|project|fact|skill|instruction",
      "content": "Clear, concise fact statement in third person",
      "confidence": 0.95
    }
  ]
}
If there are no long-term facts or preferences to remember, return {"memories": []}.
"""


class MemoryManager:
    def __init__(self):
        pass

    # ------------------------------------------------------------------
    # Asynchronous background memory extraction
    # ------------------------------------------------------------------
    def extract_memories_async(
        self,
        query: str,
        assistant_response: str,
        session_id: int = None,
        llm_client: LLMClient = None,
        model: str = None,
    ):
        """Dispatches memory extraction to a background thread to prevent UI freezing."""
        if not config.ENABLE_LONG_TERM_MEMORY:
            return

        thread = threading.Thread(
            target=self._extract_worker,
            args=(query, assistant_response, session_id, llm_client, model),
            daemon=True,
        )
        thread.start()

    def _extract_worker(
        self,
        query: str,
        assistant_response: str,
        session_id: int,
        llm_client: LLMClient,
        model: str,
    ):
        if not llm_client or not model:
            return

        # Skip very short or generic queries
        if len(query.strip()) < 8 and len(assistant_response.strip()) < 20:
            return

        messages = [
            {"role": "system", "content": MEMORY_EXTRACTION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"User: {query}\nAssistant: {assistant_response[:1000]}",
            },
        ]

        try:
            data = llm_client.chat_json(
                model=model,
                messages=messages,
                temperature=config.GATE_TEMP,
                max_tokens=config.MAX_TOKENS_GATE,
            )
            memories = data.get("memories", [])
            for m in memories:
                conf = float(m.get("confidence", 1.0))
                if conf >= config.MEMORY_CONFIDENCE_THRESHOLD:
                    key = m.get("key", "").strip()
                    content = m.get("content", "").strip()
                    category = m.get("category", "fact").strip()
                    if key and content:
                        db.add_or_update_memory(
                            key=key,
                            content=content,
                            category=category,
                            confidence=conf,
                            session_id=session_id,
                        )
        except (LMStudioError, Exception):
            # Fail silently in the background — memory extraction is non-blocking
            pass

    # ------------------------------------------------------------------
    # Semantic memory retrieval for system prompt injection
    # ------------------------------------------------------------------
    def retrieve_relevant_memories(
        self, query: str, top_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves the most relevant memories from SQLite using hybrid scoring
        against the user's current query.
        """
        if not config.ENABLE_LONG_TERM_MEMORY:
            return []

        all_memories = db.list_memories()
        if not all_memories:
            return []

        limit = top_k or config.MAX_MEMORY_ITEMS_IN_PROMPT
        if len(all_memories) <= limit:
            return all_memories

        # Rank memories using search_engine hybrid scoring
        try:
            from search_engine import hybrid_score

            texts = [f"{m['category']}: {m['key']} - {m['content']}" for m in all_memories]
            scores = hybrid_score(query, texts)
            ranked = sorted(zip(all_memories, scores), key=lambda x: x[1], reverse=True)
            return [m for m, score in ranked[:limit] if score > 0.15]
        except Exception:
            # Fallback: return most recently updated memories
            return all_memories[:limit]

    # ------------------------------------------------------------------
    # Formatting for system prompt
    # ------------------------------------------------------------------
    def format_memory_context(self, memories: List[Dict[str, Any]]) -> str:
        """Formats a list of memories into a clear markdown system instructions block."""
        if not memories:
            return ""

        lines = ["## User Profile & Long-Term Memory (Second Brain)"]
        lines.append("The following persistent facts and preferences about the user are known:")
        for m in memories:
            cat = m.get("category", "fact").upper()
            content = m.get("content", "")
            lines.append(f"- [{cat}] {content}")
        lines.append("")
        return "\n".join(lines)
