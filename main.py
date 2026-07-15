"""
main.py — Gayatri AI v5.0
Flet app entrypoint. Wires together config, llm_client, search_engine,
context_manager, db, and ui_components into the full desktop assistant.
Run with: python main.py   (or: flet run main.py)
"""

import os
import glob
import threading
import flet as ft

import config
import db
import ui_components as ui
from llm_client import LLMClient, LMStudioError
from search_engine import (
    needs_search, gen_keywords_enhanced, multi_search_enhanced, crawl_site,
    choose_length, build_grounded_messages, extract_urls,
)
from context_manager import ContextManager, summarize_history


def main(page: ft.Page):
    # ------------------------------------------------------------------
    # Initial setup & state
    # ------------------------------------------------------------------
    ui.set_active_theme(config.THEME_DARK)
    
    db.init_db()
    llm_client = LLMClient()
    context_manager = ContextManager()

    state = {
        "session_id": None,
        "search_mode": config.DEFAULT_SEARCH_MODE,
        "model": config.DEFAULT_MODEL,
        "model_ids": [],
        "is_generating": False,
        "stop_requested": False,
        "sidebar_expanded": {"recent": True, "context": False, "session_files": False},
        "sidebar_collapsed": False,
        "theme_mode": "dark",
        "theme_colors": config.THEME_DARK,
    }

    # ------------------------------------------------------------------
    # Page setup
    # ------------------------------------------------------------------
    page.title = "Gayatri AI"
    page.bgcolor = ui.T["bg"]
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.window.min_width = 800
    page.window.min_height = 600
    page.window.width = 1280
    page.window.height = 820
    page.window.maximized = True
    page.window.center()

    # ------------------------------------------------------------------
    # Theme Toggler
    # ------------------------------------------------------------------
    def toggle_theme(e=None):
        if state["theme_mode"] == "dark":
            state["theme_mode"] = "light"
            state["theme_colors"] = config.THEME_LIGHT
            page.theme_mode = ft.ThemeMode.LIGHT
        else:
            state["theme_mode"] = "dark"
            state["theme_colors"] = config.THEME_DARK
            page.theme_mode = ft.ThemeMode.DARK
        
        ui.set_active_theme(state["theme_colors"])
        page.bgcolor = ui.T["bg"]
        chat_history_wrapper.bgcolor = ui.T["bg"]
        main_area.bgcolor = ui.T["bg"]
        
        rebuild_sidebar()
        rebuild_input_dock()
        page.update()

    # ------------------------------------------------------------------
    # Stable, persistent controls (mutated in place, never reparented)
    # ------------------------------------------------------------------
    chat_history = ft.Column(
        expand=True, spacing=25, scroll=ft.ScrollMode.AUTO,
    )
    
    # Starting padding scales with screen width
    chat_history_wrapper = ft.Container(
        content=chat_history, expand=True, bgcolor=ui.T["bg"],
        padding=ft.padding.symmetric(horizontal=80, vertical=30),
    )
    status_banner = ft.Container(visible=False)
    
    top_bar_status_dot = ft.Container(
        width=10, height=10, border_radius=5, bgcolor=ui.T["accent_secondary"]
    )
    
    top_bar = ft.Container(
        content=ft.Row(
            [
                ft.Row(
                    [
                        top_bar_status_dot,
                        ft.Text("SYSTEM ONLINE", size=10, color=ui.T["text_secondary"], weight=ft.FontWeight.BOLD),
                    ],
                    spacing=8,
                ),
                ft.Container(expand=True),
                ft.Text("Qwen 2.5 7B", size=11, color=ui.T["text_primary"], weight=ft.FontWeight.W_600, key="model_label"),
            ],
            alignment=ft.MainAxisAlignment.START,
        ),
        padding=ft.padding.symmetric(horizontal=30, vertical=15),
    )

    # Sidebar container WITH DECELERATE TRANSITION ANIMATION
    sidebar_container = ft.Container(
        width=config.SIDEBAR_WIDTH,
        bgcolor=ui.T["surface"],
        animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
        border=ft.border.only(right=ft.border.BorderSide(1, ui.T["border"])),
    )
    
    input_dock_holder = ft.Container()

    main_column = ft.Column(
        [top_bar, status_banner, chat_history_wrapper, input_dock_holder],
        expand=True, spacing=0,
    )
    main_area = ft.Container(expand=True, bgcolor=ui.T["bg"], content=main_column)
    root_row = ft.Row([sidebar_container, main_area], expand=True, spacing=0)

    # ------------------------------------------------------------------
    # Dynamic Screen-Resizing Handler
    # ------------------------------------------------------------------
    def handle_page_resize(e):
        w = page.window.width
        if not w:
            return
            
        # 1. Sidebar Auto-Collapse logic: collapse if narrow (< 980px)
        if w < 980 and not state["sidebar_collapsed"]:
            state["sidebar_collapsed"] = True
            rebuild_sidebar()
        elif w >= 980 and state["sidebar_collapsed"]:
            state["sidebar_collapsed"] = False
            rebuild_sidebar()

        # 2. Responsive padding inside chat canvas
        h_padding = 80 if w > 1200 else (40 if w > 1000 else 20)
        chat_history_wrapper.padding = ft.padding.symmetric(horizontal=h_padding, vertical=20)
        
        # 3. Re-draw components that adapt dynamically to window width
        rebuild_input_dock()
        page.update()

    page.on_resized = handle_page_resize

    # ------------------------------------------------------------------
    # LM Studio connectivity + model list
    # ------------------------------------------------------------------
    def refresh_models(show_banner_on_fail: bool = True):
        try:
            models = llm_client.list_models()
            state["model_ids"] = models
            if models and state["model"] not in models:
                state["model"] = models[0]
            status_banner.visible = False
            top_bar_status_dot.bgcolor = ui.T["accent_secondary"]
            # Update model label
            model_lbl = top_bar.content.controls[2]
            model_lbl.value = state["model"] or "No model loaded"
        except LMStudioError as e:
            state["model_ids"] = []
            top_bar_status_dot.bgcolor = ui.T["accent_highlight"]
            if show_banner_on_fail:
                status_banner.content = ft.Row(
                    [
                        ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ui.T["accent_highlight"], size=16),
                        ft.Text(str(e), color=ui.T["text_primary"], size=12, expand=True),
                        ft.TextButton("Refresh", on_click=lambda e: (refresh_models(), page.update())),
                    ],
                    spacing=8,
                )
                status_banner.padding = 10
                status_banner.bgcolor = ft.Colors.with_opacity(0.15, ui.T["accent_highlight"])
                status_banner.border_radius = 8
                status_banner.margin = ft.margin.symmetric(horizontal=20, vertical=8)
                status_banner.visible = True

    # ------------------------------------------------------------------
    # Session helpers
    # ------------------------------------------------------------------
    def ensure_session():
        if state["session_id"] is None:
            state["session_id"] = db.create_session()

    def show_empty_state_if_needed():
        if not chat_history.controls:
            chat_history.controls.append(ui.empty_state(on_suggestion_click=handle_send))

    def new_chat(e=None):
        state["session_id"] = db.create_session()
        chat_history.controls.clear()
        show_empty_state_if_needed()
        rebuild_sidebar()
        page.update()

    def load_session(session_id: int):
        state["session_id"] = session_id
        chat_history.controls.clear()
        for m in db.get_messages(session_id):
            if m["role"] == "user":
                chat_history.controls.append(ft.Row([ui.user_bubble(m["content"])], alignment=ft.MainAxisAlignment.END))
            elif m["role"] == "assistant":
                chat_history.controls.append(
                    ui.ai_message_block(
                        m["content"], sources=m["sources"], chunks_used=m["md_chunks_used"],
                        on_copy=lambda content=m["content"]: page.set_clipboard(content),
                        on_regenerate=lambda: None,
                    )
                )
        show_empty_state_if_needed()
        rebuild_sidebar()
        page.update()

    def delete_session(session_id: int):
        db.delete_session(session_id)
        if state["session_id"] == session_id:
            state["session_id"] = None
            chat_history.controls.clear()
        rebuild_sidebar()
        page.update()

    # ------------------------------------------------------------------
    # Sidebar rebuild WITH ANIMATION MUTATION IN PLACE
    # ------------------------------------------------------------------
    def toggle_sidebar_collapse(e=None):
        state["sidebar_collapsed"] = not state["sidebar_collapsed"]
        rebuild_sidebar()
        page.update()

    def rebuild_sidebar():
        sidebar_container.width = 56 if state["sidebar_collapsed"] else config.SIDEBAR_WIDTH
        sidebar_container.bgcolor = ui.T["surface"]
        sidebar_container.border = ft.border.only(right=ft.border.BorderSide(1, ui.T["border"]))

        # Build threads
        sessions = db.list_sessions()
        session_items = [
            ui.session_list_item(
                s["title"], s["updated_at"][:16].replace("T", " "),
                s["id"] == state["session_id"],
                on_click=lambda sid=s["id"]: load_session(sid),
                on_delete=lambda sid=s["id"]: delete_session(sid),
            )
            for s in sessions
        ]

        # Build global Context Center toggles
        context_rows = [
            ui.context_toggle_row(
                fn, context_manager.files[fn].enabled,
                on_change=lambda e, fname=fn: (
                    context_manager.set_enabled(fname, e.control.value), page.update()
                ),
            )
            for fn in context_manager.list_files()
        ]

        # Build session-specific file toggles
        session_file_rows = [
            ui.session_context_toggle_row(
                f["id"], f["filename"], bool(f["enabled"]),
                on_change=lambda e, fid=f["id"]: (
                    db.set_session_context_file_enabled(fid, e.control.value), page.update()
                ),
                on_delete=lambda fid: (db.delete_session_context_file(fid), rebuild_sidebar(), page.update()),
            )
            for f in context_manager.list_session_files(state["session_id"])
        ]

        stats = db.get_stats(state["session_id"]) if state["session_id"] else {
            "keywords_generated": 0, "searches_performed": 0, "sources_found": 0, "pages_crawled": 0
        }

        # Use helper to render inner Column and set it directly
        temp_sidebar = ui.build_sidebar(
            session_items=session_items,
            context_rows=context_rows,
            session_file_rows=session_file_rows,
            stats=stats,
            on_new_chat=new_chat,
            on_open_settings=open_settings,
            on_add_session_file=handle_attach_session_file,
            expanded=state["sidebar_expanded"],
            on_toggle_expand=lambda key, is_expanded: state["sidebar_expanded"].update({key: is_expanded}),
            collapsed=state["sidebar_collapsed"],
            on_toggle_collapse=toggle_sidebar_collapse,
            on_toggle_theme=toggle_theme,
        )
        sidebar_container.content = temp_sidebar.content
        sidebar_container.padding = temp_sidebar.padding

    # ------------------------------------------------------------------
    # Settings dialog (with validation)
    # ------------------------------------------------------------------
    def open_settings(e=None):
        def on_save(base_url, embed_model, search_count_str, ctx_budget_str, dialog_ref):
            try:
                search_count = int(search_count_str) if search_count_str else config.SEARCH_RESULTS_PER_QUERY
                ctx_budget = int(ctx_budget_str) if ctx_budget_str else config.MAX_MD_TOKENS
                
                llm_client.base_url = base_url.rstrip("/")
                config.SEARCH_RESULTS_PER_QUERY = search_count
                config.MAX_MD_TOKENS = ctx_budget
                page.close(dialog_ref)
                status_banner.visible = False
                refresh_models()
                page.update()
            except ValueError:
                status_banner.content = ft.Text(
                    "Error: Search Result Count and Context Token Budget must be valid integers.",
                    color=ui.T["text_primary"], size=12
                )
                status_banner.padding = 10
                status_banner.bgcolor = ft.Colors.with_opacity(0.15, ui.T["accent_highlight"])
                status_banner.border_radius = 8
                status_banner.margin = ft.margin.symmetric(horizontal=20, vertical=8)
                status_banner.visible = True
                page.close(dialog_ref)
                page.update()

        dialog = ui.settings_dialog(
            llm_client.base_url, config.EMBED_MODEL,
            config.SEARCH_RESULTS_PER_QUERY, config.MAX_MD_TOKENS, on_save,
        )
        page.open(dialog)

    # ------------------------------------------------------------------
    # Input dock rebuild
    # ------------------------------------------------------------------
    def rebuild_input_dock():
        new_dock = ui.input_dock(
            on_send=handle_send,
            on_stop=handle_stop,
            on_attach=handle_attach,
            model_ids=state["model_ids"],
            selected_model=state["model"],
            on_model_change=lambda e: (state.update({"model": e.control.value}), refresh_models(False), page.update()),
            current_search_mode=state["search_mode"],
            on_search_mode_change=lambda mode: (state.update({"search_mode": mode}), rebuild_input_dock(), page.update()),
            is_generating=state["is_generating"],
            window_width=page.window.width if page.window.width else 1200,
        )
        main_column.controls[3] = new_dock
        input_dock_holder.content = new_dock

    def handle_attach(e=None):
        def on_result(result: ft.FilePickerResultEvent):
            if result.files:
                context_manager.add_context_file(result.files[0].path)
                rebuild_sidebar()
                page.update()

        picker = ft.FilePicker(on_result=on_result)
        page.overlay.append(picker)
        page.update()
        picker.pick_files(allow_multiple=False, allowed_extensions=["md"])

    def handle_attach_session_file():
        ensure_session()

        def on_result(result: ft.FilePickerResultEvent):
            if not result.files:
                return
            picked = result.files[0]
            try:
                with open(picked.path, "r", encoding="utf-8") as f:
                    content = f.read()
                db.add_session_context_file(state["session_id"], picked.name, content)

                if db.count_session_context_files(state["session_id"]) > db.SOFT_FILE_COUNT_WARNING:
                    status_banner.content = ft.Text(
                        f"This thread has {db.count_session_context_files(state['session_id'])} "
                        f"context files — relevance scoring may slow down with many files.",
                        color=ui.T["text_primary"], size=12,
                    )
                    status_banner.padding = 10
                    status_banner.bgcolor = ft.Colors.with_opacity(0.15, ui.T["accent_secondary"])
                    status_banner.border_radius = 8
                    status_banner.margin = ft.margin.symmetric(horizontal=20, vertical=8)
                    status_banner.visible = True
            except db.SessionFileTooLargeError as err:
                status_banner.content = ft.Text(str(err), color=ui.T["text_primary"], size=12)
                status_banner.padding = 10
                status_banner.bgcolor = ft.Colors.with_opacity(0.15, ui.T["accent_highlight"])
                status_banner.border_radius = 8
                status_banner.margin = ft.margin.symmetric(horizontal=20, vertical=8)
                status_banner.visible = True
            except OSError as err:
                status_banner.content = ft.Text(f"Could not read file: {err}", color=ui.T["text_primary"], size=12)
                status_banner.padding = 10
                status_banner.bgcolor = ft.Colors.with_opacity(0.15, ui.T["accent_highlight"])
                status_banner.border_radius = 8
                status_banner.margin = ft.margin.symmetric(horizontal=20, vertical=8)
                status_banner.visible = True

            rebuild_sidebar()
            page.update()

        picker = ft.FilePicker(on_result=on_result)
        page.overlay.append(picker)
        page.update()
        picker.pick_files(allow_multiple=False, allowed_extensions=["md"])

    def handle_stop(e=None):
        state["stop_requested"] = True

    # ------------------------------------------------------------------
    # Core send/generate pipeline with LIVE PROGRESS ANIMATIONS
    # ------------------------------------------------------------------
    def handle_send(query: str):
        query = (query or "").strip()
        if not query or state["is_generating"]:
            return
        if not state["model"]:
            status_banner.content = ft.Text("No model selected. Load a model in LM Studio and click Refresh.",
                                              color=ui.T["text_primary"], size=12)
            status_banner.padding = 10
            status_banner.bgcolor = ft.Colors.with_opacity(0.15, ui.T["accent_highlight"])
            status_banner.border_radius = 8
            status_banner.margin = ft.margin.symmetric(horizontal=20, vertical=8)
            status_banner.visible = True
            page.update()
            return

        ensure_session()
        existing_messages = db.get_messages(state["session_id"])
        is_first_message = len(existing_messages) == 0

        if is_first_message:
            chat_history.controls.clear()

        # Add user bubble right-aligned
        db.add_message(state["session_id"], "user", query)
        chat_history.controls.append(ft.Row([ui.user_bubble(query)], alignment=ft.MainAxisAlignment.END))

        if is_first_message:
            title = query.strip().replace("\n", " ")
            if len(title) > 42:
                title = title[:42].rstrip() + "..."
            db.rename_session(state["session_id"], title)
            rebuild_sidebar()

        # Instantiate the LIVE response block
        live_block = ui.LiveResponseBlock(
            on_copy=lambda: page.set_clipboard(live_block.answer_markdown.value),
            on_regenerate=lambda: handle_send(query),
        )
        chat_history.controls.append(live_block)
        page.update()
        
        # Scroll to bottom on new query
        chat_history.scroll_to(offset=-1, duration=200)

        state["is_generating"] = True
        state["stop_requested"] = False
        rebuild_input_dock()
        page.update()

        thread = threading.Thread(target=run_generation, args=(query, live_block), daemon=True)
        thread.start()

    def run_generation(query: str, live_block: ui.LiveResponseBlock):
        # Local helper to write a step and auto-scroll the chat
        def add_step_and_scroll(text: str, status: str):
            live_block.add_step(text, status)
            chat_history.scroll_to(offset=-1, duration=150)

        sources = []
        keywords = []
        crawl_status = ""
        page_docs = []

        try:
            urls_in_query = extract_urls(query)

            do_url_crawl = False
            do_search = False

            # STEP 1: Decide search requirements
            add_step_and_scroll("Deciding search requirements...", "running")

            if state["search_mode"] == config.SEARCH_MODE_URL_ONLY and urls_in_query:
                do_url_crawl = True
            elif state["search_mode"] == config.SEARCH_MODE_FORCE_WEB:
                do_search = True
            elif state["search_mode"] == config.SEARCH_MODE_FORCE_NONE:
                pass
            else:
                if urls_in_query and config.ENABLE_URL_DIRECT_CRAWL:
                    do_url_crawl = True
                else:
                    decision, confidence, reason, category = needs_search(query, llm_client, state["model"])
                    do_search = decision

            add_step_and_scroll("Deciding search requirements...", "done")

            category = "unclear"

            # STEP 2: Scrape / Web Search
            if do_url_crawl:
                add_step_and_scroll(f"Crawling website: {urls_in_query[0]}...", "running")
                page_docs = crawl_site(urls_in_query[0])
                add_step_and_scroll(f"Crawling website: {urls_in_query[0]}...", "done")
                
                add_step_and_scroll(f"Indexed {len(page_docs)} document chunks", "done")
                db.increment_stats(state["session_id"], pages_crawled=len(page_docs))

            elif do_search:
                add_step_and_scroll("Generating search keywords...", "running")
                keywords = gen_keywords_enhanced(query, llm_client, state["model"])
                add_step_and_scroll("Generating search keywords...", "done")
                db.increment_stats(state["session_id"], keywords_generated=len(keywords), searches_performed=1)

                add_step_and_scroll(f"Querying web index for '{keywords[0]}'...", "running")
                sources = multi_search_enhanced(keywords)
                add_step_and_scroll(f"Querying web index for '{keywords[0]}'...", "done")
                
                add_step_and_scroll(f"Found {len(sources)} sources", "done")
                db.increment_stats(state["session_id"], sources_found=len(sources))

                # Display compact source badges instantly
                live_block.set_sources(sources)
                chat_history.scroll_to(offset=-1, duration=150)

            # STEP 3: Context Retrieval
            add_step_and_scroll("Retrieving guidelines and context files...", "running")
            all_messages = db.get_messages(state["session_id"])
            recent_count = config.HISTORY_TURNS
            older_messages = all_messages[:-recent_count] if len(all_messages) > recent_count else []
            recent_messages = all_messages[-recent_count:] if recent_count > 0 else []

            older_summary = summarize_history(
                [{"role": m["role"], "content": m["content"]} for m in older_messages],
                max_turns=len(older_messages),
            ) if older_messages else ""

            conversation_turns = [
                {"role": m["role"], "content": m["content"]} for m in recent_messages
                if m["role"] in ("user", "assistant")
            ]
            if conversation_turns and conversation_turns[-1]["content"] == query:
                conversation_turns = conversation_turns[:-1]

            system_context, chunks_used = context_manager.build_system_context(
                query, history_summary=older_summary, session_id=state["session_id"],
            )
            add_step_and_scroll("Retrieving guidelines and context files...", "done")
            
            if chunks_used:
                add_step_and_scroll(f"Ranked and selected {len(chunks_used)} document context chunk(s)", "done")

            # STEP 4: Streaming Answer
            target_words = choose_length(query, category=category)
            messages = build_grounded_messages(
                query, system_context, sources=sources, page_docs=page_docs, target_words=target_words,
                conversation_turns=conversation_turns,
            )

            # Clear typing and prepare streaming
            live_block.set_answer("")

            full_text = ""
            for chunk in llm_client.stream_chat(state["model"], messages):
                if state["stop_requested"]:
                    break
                full_text += chunk
                live_block.set_answer(full_text)
                
                # Dynamic scroll to follow response pointer
                chat_history.scroll_to(offset=-1, duration=100)

            # Generate related questions to match mockup suggestions
            related_questions = [
                f"Can you expand on {query[:25]}?",
                "What is the source data?",
            ]
            
            # Finalize: collapses the reasoning tile, registers suggest options
            live_block.finalize(
                full_text, 
                related_questions=related_questions,
                on_related_click=handle_send
            )
            chat_history.scroll_to(offset=-1, duration=200)

            db.add_message(state["session_id"], "assistant", full_text,
                             sources=sources, md_chunks_used=chunks_used)

        except LMStudioError as e:
            live_block.set_answer(f"⚠️ {e}")
        except Exception as e:
            live_block.set_answer(f"⚠️ Unexpected error: {e}")
        finally:
            state["is_generating"] = False
            state["stop_requested"] = False
            rebuild_input_dock()
            rebuild_sidebar()
            page.update()

    # ------------------------------------------------------------------
    # Initial load
    # ------------------------------------------------------------------
    ensure_session()
    rebuild_sidebar()
    rebuild_input_dock()
    refresh_models()
    show_empty_state_if_needed()

    page.add(root_row)
    page.update()


if __name__ == "__main__":
    ft.app(target=main)