"""
agent.py — Gayatri AI v5.0
Autonomous Agent Mode Engine.
Accepts a high-level user goal, formulates a structured step-by-step action plan,
dispatches tools (Web Search, Web Crawl, Context/RAG, Memory Vault, Reasoning),
persists task and step state in SQLite for full resumability, and synthesizes final results.
"""

import os
import re
import json
import logging
from typing import Callable, List, Dict, Tuple, Any, Optional

import config
import db
from llm_client import LLMClient, LMStudioError
from search_engine import (
    multi_search_enhanced,
    crawl_site,
    split_sections,
    hybrid_score,
    extract_urls,
    normalize_ws,
)

logger = logging.getLogger(__name__)

PLAN_SYSTEM_PROMPT = """You are Gayatri AI's Autonomous Agent Planning Engine.
Your job is to break down a high-level user goal into an actionable, logical sequence of 2 to {max_steps} execution steps.

Available Tools:
1. "web_search": Searches DuckDuckGo for live facts, documents, software, or benchmarks.
   tool_input format: {{"query": "search query here"}}
2. "read_context": Retrieves relevant project context, rules, or workspace markdown files.
   tool_input format: {{"query": "context query here"}}
3. "memory_lookup": Searches the Second Brain / Memory Vault for stored user preferences, facts, or instructions.
   tool_input format: {{"query": "memory topic here"}}
4. "reason": Analytical or comparative step that processes previously gathered findings.
   tool_input format: {{"focus": "aspect to analyze or compare"}}

Guidelines:
- Keep the plan concise, practical, and highly focused on the user's objective.
- For research/comparison tasks, start with search/context/memory gathering before reasoning.
- Output strictly a valid JSON object matching this schema:

{{
  "thought": "Brief explanation of the strategy",
  "steps": [
    {{
      "title": "Short descriptive step title (e.g. Search for lightweight LLM models)",
      "tool": "web_search",
      "tool_input": {{"query": "best lightweight open source LLMs for laptop 2024 2025"}}
    }},
    {{
      "title": "Retrieve stored user hardware preferences",
      "tool": "memory_lookup",
      "tool_input": {{"query": "hardware laptop specifications"}}
    }},
    {{
      "title": "Analyze and compare model requirements against hardware",
      "tool": "reason",
      "tool_input": {{"focus": "RAM and VRAM compatibility"}}
    }}
  ]
}}
"""

AGENT_SYNTHESIS_SYSTEM_PROMPT = """You are Gayatri AI in Autonomous Agent Mode.
You have created and executed an action plan to fulfill the user's goal.
Review the original goal, the execution steps taken, and all collected evidence.
Produce a comprehensive, rigorous, well-structured, and highly actionable final response.

Guidelines:
- Structure the response with clear Markdown headers, bullet points, and comparative tables where appropriate.
- Clearly present findings, recommendations, and next steps.
- Reference any factual findings or sources gathered during execution.
"""

AGENT_CONVERSATIONAL_SYSTEM_PROMPT = """You are Gayatri AI in Autonomous Agent Mode 🤖.
The user sent a greeting or conversational message instead of a complex task.
Greet the user warmly in a modern, professional tone.
Explain clearly that in Agent Mode, you can take any high-level objective, autonomously break it into steps, perform live web research, crawl pages, inspect local markdown context, and synthesize in-depth solutions.
Give 3 quick, inspiring example goals the user can try (e.g. comparing AI models, planning a technical roadmap, or researching a topic).
"""

_CONVERSATIONAL_GOAL_PATTERN = re.compile(
    r"^(hi|hello|hey|greetings|good morning|good afternoon|good evening|who are you|what can you do|how are you|thanks|thank you|ok|okay|bye|help)\b",
    re.IGNORECASE,
)

_COMMON_GREETINGS = {"hi", "hello", "hey", "yo", "sup", "help", "test", "ping", "howdy"}


def is_conversational_goal(goal: str) -> bool:
    """Checks if the user input is a greeting or casual chat rather than an actionable task."""
    g = (goal or "").strip().lower()
    if not g:
        return True
    if _CONVERSATIONAL_GOAL_PATTERN.match(g):
        return True
    words = g.split()
    if len(words) <= 2 and any(w.strip("!.,?") in _COMMON_GREETINGS for w in words):
        return True
    return False


def _clean_json_response(raw_text: str) -> dict:
    """Extracts and parses JSON from model response text safely."""
    raw_text = raw_text.strip()
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
    if match:
        raw_text = match.group(1)
    else:
        obj_match = re.search(r"(\{.*\})", raw_text, re.DOTALL)
        if obj_match:
            raw_text = obj_match.group(1)
    try:
        return json.loads(raw_text)
    except Exception:
        return {}


def plan_task(
    goal: str,
    llm_client: LLMClient,
    model: str,
    max_steps: int = config.AGENT_MAX_STEPS,
) -> List[Dict[str, Any]]:
    """Prompts the LLM to generate a structured action plan for the given goal."""
    prompt = f"Goal: {goal}"
    messages = [
        {"role": "system", "content": PLAN_SYSTEM_PROMPT.format(max_steps=max_steps)},
        {"role": "user", "content": prompt},
    ]

    try:
        raw = llm_client.chat(model, messages, temperature=config.GATE_TEMP, max_tokens=600)
        data = _clean_json_response(raw)
        steps = data.get("steps", [])
        if isinstance(steps, list) and steps:
            valid_steps = []
            for s in steps[:max_steps]:
                if isinstance(s, dict) and "title" in s:
                    valid_steps.append({
                        "title": s.get("title", "Execute step"),
                        "tool": s.get("tool", "reason"),
                        "tool_input": s.get("tool_input", {}),
                    })
            if valid_steps:
                return valid_steps
    except Exception as e:
        logger.warning(f"Error in agent planning: {e}")

    # Smart fallback plan if JSON generation failed
    from search_engine import heuristic_gate
    should_search, _, _, _ = heuristic_gate(goal)

    if should_search:
        return [
            {
                "title": f"Search information for: {goal[:40]}",
                "tool": "web_search",
                "tool_input": {"query": goal},
            },
            {
                "title": "Analyze findings and synthesize answer",
                "tool": "reason",
                "tool_input": {"focus": goal},
            },
        ]
    else:
        return [
            {
                "title": f"Analyze and execute: {goal[:40]}",
                "tool": "reason",
                "tool_input": {"focus": goal},
            },
        ]


def _execute_web_search_step(
    tool_input: dict,
    session_id: int,
) -> Tuple[str, List[dict]]:
    """Executes a web search and crawl action for the agent."""
    query = ""
    if isinstance(tool_input, dict):
        query = tool_input.get("query", "")
    elif isinstance(tool_input, str):
        query = tool_input

    if not query:
        return "No search query provided.", []

    results = multi_search_enhanced([query], max_sources=config.MAX_SOURCES)
    if not results:
        return f"No web search results found for: {query}", []

    top_results = results[:config.MAX_SOURCES]
    sources = [{"title": r.get("title", ""), "href": r.get("href", ""), "body": r.get("body", "")} for r in top_results]

    # Crawl top 2 sources for deeper content
    crawled_excerpts = []
    for r in top_results[:2]:
        href = r.get("href", "")
        if href:
            text = crawl_site(href)
            if text:
                crawled_excerpts.append(f"Source [{r.get('title', href)}]: {text[:400]}")

    summary_lines = [f"- {r.get('title', 'Result')}: {r.get('body', '')[:200]}" for r in top_results[:4]]
    output_text = f"Key Findings for '{query}':\n" + "\n".join(summary_lines)
    if crawled_excerpts:
        output_text += "\n" + "\n".join(crawled_excerpts)

    db.increment_stats(session_id, searches_performed=1, sources_found=len(top_results), pages_crawled=len(crawled_excerpts))
    return output_text[:1000], sources


def _execute_context_step(
    tool_input: dict,
    context_manager: Any,
    session_id: int,
) -> Tuple[str, List[dict]]:
    """Retrieves relevant markdown / workspace context."""
    query = ""
    if isinstance(tool_input, dict):
        query = tool_input.get("query", "")
    elif isinstance(tool_input, str):
        query = tool_input

    if context_manager:
        system_context, chunks_used = context_manager.build_system_context(query, session_id=session_id)
        if chunks_used:
            return f"Retrieved context chunks ({', '.join(chunks_used)}):\n{system_context[:600]}", []
    return "No additional workspace context found.", []


def _execute_memory_step(
    tool_input: dict,
) -> Tuple[str, List[dict]]:
    """Retrieves relevant facts/memories from the Memory Vault."""
    query = ""
    if isinstance(tool_input, dict):
        query = tool_input.get("query", "")
    elif isinstance(tool_input, str):
        query = tool_input

    memories = db.list_memories()
    if not memories:
        return "No memories stored in the Memory Vault yet.", []

    matching = []
    q_words = set(re.findall(r"\w+", (query or "").lower()))
    for m in memories:
        content_lower = (m.get("key", "") + " " + m.get("content", "")).lower()
        if any(w in content_lower for w in q_words) or not q_words:
            matching.append(f"[{m.get('category', 'fact')}] {m.get('key')}: {m.get('content')}")

    if matching:
        return "Relevant Second Brain Memories:\n" + "\n".join(matching[:4]), []
    return "No matching memories found for query.", []


def _execute_reason_step(
    tool_input: dict,
    gathered_context: str,
    llm_client: LLMClient,
    model: str,
) -> Tuple[str, List[dict]]:
    """Performs an intermediate reasoning or calculation step."""
    focus = ""
    if isinstance(tool_input, dict):
        focus = tool_input.get("focus", "")
    elif isinstance(tool_input, str):
        focus = tool_input

    context_tail = gathered_context[-1200:] if len(gathered_context) > 1200 else gathered_context
    prompt = f"Focus / Analysis Target: {focus}\n\nEvidence & Information Collected So Far:\n{context_tail}\n\nPlease synthesize a concise analytical summary addressing the focus target."
    messages = [
        {"role": "system", "content": "You are a concise analytical reasoning assistant."},
        {"role": "user", "content": prompt},
    ]

    try:
        res = llm_client.chat(model, messages, temperature=config.STREAM_TEMP, max_tokens=400)
        return res.strip(), []
    except Exception as e:
        return f"Reasoning analysis completed on: {focus}", []


def execute_agent_task(
    goal: str,
    llm_client: LLMClient,
    model: str,
    session_id: int,
    context_manager: Any = None,
    system_context: str = "",
    step_callback: Optional[Callable[[str, str], None]] = None,
    stop_checker: Optional[Callable[[], bool]] = None,
) -> Tuple[Optional[str], List[dict], List[str], List[dict]]:
    """
    Main entry point for Agent Mode execution.
    Returns: (cancel_message, accumulated_sources, collected_evidence, synthesis_messages)
    """
    def is_stopped() -> bool:
        return stop_checker() if stop_checker else False

    def emit_step(title: str, status: str):
        if step_callback:
            step_callback(title, status)

    if is_stopped():
        return "⏹️ Agent execution cancelled.", [], [], []

    # Fast-path for conversational greetings / smalltalk
    if is_conversational_goal(goal):
        task_id = db.create_agent_task(session_id, goal)
        emit_step("Agent Mode active 🤖", "done")
        db.update_agent_task_status(task_id, "completed")
        messages = [
            {"role": "system", "content": (system_context + "\n\n" if system_context else "") + AGENT_CONVERSATIONAL_SYSTEM_PROMPT},
            {"role": "user", "content": goal},
        ]
        return None, [], [], messages

    # 1. Check for existing pending task or create new one
    task = db.get_latest_agent_task(session_id)
    if task and task.get("status") in ("pending", "running") and task.get("goal") == goal.strip():
        task_id = task["id"]
        steps = db.get_agent_steps(task_id)
    else:
        task_id = db.create_agent_task(session_id, goal)
        emit_step("Formulating step-by-step action plan...", "running")
        planned_steps = plan_task(goal, llm_client, model)
        db.create_agent_steps(task_id, planned_steps)
        steps = db.get_agent_steps(task_id)
        emit_step(f"Created action plan with {len(steps)} steps", "done")

    db.update_agent_task_status(task_id, "running")

    accumulated_sources: List[dict] = []
    collected_evidence: List[str] = []

    # 2. Sequential Step Execution Loop
    for step in steps:
        if is_stopped():
            db.update_agent_task_status(task_id, "cancelled")
            return "⏹️ Agent execution stopped by user.", accumulated_sources, collected_evidence, []

        step_id = step["id"]
        step_title = step.get("title", "Executing step")
        tool = step.get("tool", "reason")
        status = step.get("status", "pending")
        tool_input_raw = step.get("tool_input", "{}")

        # Skip already completed steps (resumability)
        if status == "completed":
            output = step.get("tool_output", "")
            if output:
                collected_evidence.append(f"### {step_title} (Completed)\n{output}")
            emit_step(f"{step_title} (Restored)", "done")
            continue

        try:
            tool_input = json.loads(tool_input_raw) if isinstance(tool_input_raw, str) else tool_input_raw
        except Exception:
            tool_input = {"query": tool_input_raw}

        emit_step(step_title, "running")
        db.update_agent_step(step_id, "running")

        step_output = ""
        step_sources: List[dict] = []

        try:
            if tool == "web_search":
                step_output, step_sources = _execute_web_search_step(tool_input, session_id)
            elif tool == "read_context":
                step_output, step_sources = _execute_context_step(tool_input, context_manager, session_id)
            elif tool == "memory_lookup":
                step_output, step_sources = _execute_memory_step(tool_input)
            elif tool == "reason":
                context_so_far = "\n\n".join(collected_evidence)
                step_output, step_sources = _execute_reason_step(tool_input, context_so_far, llm_client, model)
            else:
                step_output = f"Step executed: {step_title}"

            # Deduplicate and accumulate sources
            for s in step_sources:
                if not any(existing.get("href") == s.get("href") for existing in accumulated_sources):
                    accumulated_sources.append(s)

            collected_evidence.append(f"### {step_title}\n{step_output}")
            db.update_agent_step(step_id, "completed", tool_output=step_output)
            emit_step(step_title, "done")

        except Exception as e:
            logger.error(f"Error executing agent step '{step_title}': {e}")
            db.update_agent_step(step_id, "failed", tool_output=f"Error: {e}")
            emit_step(f"{step_title} (Error: {e})", "done")

    if is_stopped():
        db.update_agent_task_status(task_id, "cancelled")
        return "⏹️ Agent execution stopped by user.", accumulated_sources, collected_evidence, []

    db.update_agent_task_status(task_id, "completed")
    emit_step("Synthesizing comprehensive final answer...", "running")

    # 3. Build Final Synthesis Messages with capped context
    evidence_block = "\n\n".join([e[:800] for e in collected_evidence])
    user_synthesis_content = f"""Goal: {goal}

Plan & Execution Evidence:
{evidence_block}

Please provide the final comprehensive, well-structured response based on the completed plan."""

    messages = [
        {"role": "system", "content": (system_context + "\n\n" if system_context else "") + AGENT_SYNTHESIS_SYSTEM_PROMPT},
        {"role": "user", "content": user_synthesis_content},
    ]

    return None, accumulated_sources, collected_evidence, messages
