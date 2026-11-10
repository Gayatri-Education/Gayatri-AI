"""
ui_components.py — Gayatri AI v5.0
Reusable Flet widgets. Composite structure borrows Perplexity's per-message
layout (sources -> reasoning accordion -> markdown answer -> action bar) and
Gemini's two-row input dock (input line + mode/model controls line), fully
re-skinned onto our config.THEME dark glassmorphic palette (Section 6.1)
instead of Flet's Material dynamic colors. No hardcoded colors — everything
pulled from config.
"""

import flet as ft

import config

# Dynamic theme routing to support Dark/Light mode on the fly
_current_theme = config.THEME_DARK

def set_active_theme(theme_colors: dict):
    global _current_theme
    _current_theme = theme_colors

class DynamicThemeDict(dict):
    def __getitem__(self, key):
        return _current_theme[key]
    def get(self, key, default=None):
        return _current_theme.get(key, default)
    def __contains__(self, key):
        return key in _current_theme

T = DynamicThemeDict()


# ---------------------------------------------------------------------------
# Chat bubbles
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Empty-state welcome screen — shown when a thread has no messages yet,
# instead of a blank canvas. Suggestion chips reuse suggested_followups_row's
# on_select signature so main.py can wire the same handler for both.
# ---------------------------------------------------------------------------
def empty_state(on_suggestion_click=None) -> ft.Container:
    suggestions = [
        "Summarize a URL for me",
        "What's the latest news on AI?",
        "Explain a concept simply",
    ]

    suggestion_chips = [
        ft.Container(
            content=ft.Text(s, size=12.5, color=T["text_primary"]),
            padding=ft.padding.symmetric(horizontal=14, vertical=9),
            border_radius=999,
            bgcolor=ft.Colors.with_opacity(0.3, T["surface"]),
            border=ft.border.all(1, T["border"]),
            ink=True,
            on_click=(lambda e, q=s: on_suggestion_click(q)) if on_suggestion_click else None,
        )
        for s in suggestions
    ]

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    width=56, height=56, border_radius=28,
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.top_left, end=ft.alignment.bottom_right,
                        colors=[T["accent_primary"], T["accent_highlight"]],
                    ),
                    content=ft.Icon(ft.Icons.AUTO_AWESOME, size=28, color=config.THEME_DARK["text_primary"]),
                    alignment=ft.alignment.center,
                ),
                ft.Container(height=16),
                ft.Text("What can I help with?", size=20, weight=ft.FontWeight.BOLD,
                         color=T["text_primary"], font_family=config.FONT_FAMILY),
                ft.Container(height=4),
                ft.Text("Ask a question, paste a URL to analyze, or attach context for this thread.",
                         size=13, color=T["text_secondary"], text_align=ft.TextAlign.CENTER),
                ft.Container(height=20),
                ft.Row(suggestion_chips, wrap=True, spacing=8, run_spacing=8,
                        alignment=ft.MainAxisAlignment.CENTER),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,
        expand=True,
        padding=40,
    )


def user_bubble(content: str) -> ft.Container:
    return ft.Container(
        content=ft.Text(content, size=15, color=config.THEME_DARK["text_primary"],
                         font_family=config.FONT_FAMILY, selectable=True),
        padding=15,
        border_radius=12,
        bgcolor=T["accent_primary"],
        alignment=ft.alignment.center_right,
        margin=ft.margin.only(left=80, top=10, bottom=10),
        animate_opacity=250,
        animate_scale=250,
        shadow=ft.BoxShadow(blur_radius=14, color=ft.Colors.with_opacity(0.25, T["accent_primary"])),
    )


def _sparkle_avatar() -> ft.Container:
    return ft.Container(
        width=20, height=20, border_radius=10,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left, end=ft.alignment.bottom_right,
            colors=[T["accent_primary"], T["accent_highlight"]],
        ),
        content=ft.Icon(ft.Icons.AUTO_AWESOME, size=10, color=config.THEME_DARK["text_primary"]),
        alignment=ft.alignment.center,
    )


def ai_bubble(content: str, streaming: bool = False) -> ft.Row:
    """Minimal AI turn — used for the live-streaming placeholder before a
    response finishes; once complete, main.py swaps this for ai_message_block."""
    bubble = ft.Container(
        content=ft.Text(
            content or ("Thinking..." if streaming else ""),
            color=T["text_primary"], size=14, font_family=config.FONT_FAMILY, selectable=True,
        ),
        padding=ft.padding.symmetric(horizontal=16, vertical=12),
        border_radius=config.BORDER_RADIUS,
        bgcolor=ft.Colors.with_opacity(0.5, T["surface"]),
        border=ft.border.all(1, T["border"]),
        expand=True,
        animate_opacity=250,
    )
    return ft.Row([_sparkle_avatar(), bubble], alignment=ft.MainAxisAlignment.START,
                   vertical_alignment=ft.CrossAxisAlignment.START, spacing=10)


# ---------------------------------------------------------------------------
# Citation chips + source cards (Perplexity-style)
# ---------------------------------------------------------------------------
def citation_chip(number: int, domain: str, on_click=None) -> ft.Container:
    return ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Text(str(number), size=9, color=config.THEME_DARK["text_primary"], weight=ft.FontWeight.BOLD),
                    width=14, height=14, border_radius=7, bgcolor=T["accent_secondary"],
                    alignment=ft.alignment.center,
                ),
                ft.Text(domain, size=11, color=T["text_primary"]),
            ],
            spacing=5, tight=True,
        ),
        padding=ft.padding.symmetric(horizontal=10, vertical=5),
        border_radius=20,
        bgcolor=ft.Colors.with_opacity(0.12, T["text_primary"]),
        border=ft.border.all(1, T["border"]),
        ink=True,
        on_click=on_click,
    )


def citation_strip(sources: list[dict]) -> ft.Row:
    import tldextract
    chips = []
    for i, s in enumerate(sources, 1):
        href = s.get("href", "")
        ext = tldextract.extract(href) if href else None
        domain = f"{ext.domain}.{ext.suffix}" if ext and ext.domain else "source"
        chips.append(citation_chip(i, domain, on_click=(lambda e, h=href: e.page.launch_url(h)) if href else None))
    return ft.Row(chips, wrap=True, spacing=6, run_spacing=6)


# ---------------------------------------------------------------------------
# Follow-up suggestion chips (Perplexity-Style Related Queries)
# ---------------------------------------------------------------------------
def suggested_followups_row(questions: list[str], on_select) -> ft.Column:
    if not questions:
        return ft.Column([])
    rows = [
        ft.Container(
            content=ft.Row(
                [ft.Icon(ft.Icons.ADD, size=13, color=T["accent_primary"]),
                 ft.Text(q, size=12.5, color=T["text_primary"], expand=True,
                          max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)],
                spacing=8,
            ),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            border_radius=8,
            border=ft.border.all(1, T["border"]),
            bgcolor=ft.Colors.with_opacity(0.04, T["text_primary"]),
            ink=True,
            on_click=lambda e, question=q: on_select(question),
        )
        for q in questions
    ]
    return ft.Column(
        [
            ft.Text("Related Queries", size=11, color=T["text_secondary"], weight=ft.FontWeight.BOLD),
            ft.Column(rows, spacing=6),
        ],
        spacing=8,
    )


# ---------------------------------------------------------------------------
# Thinking / Searching accordion ("Research & Scrape Steps")
# ---------------------------------------------------------------------------
def thinking_accordion(keywords: list[str], sources_found: int, crawl_status: str,
                        chunks_used: list[str] = None) -> ft.ExpansionTile:
    rows = []
    if keywords:
        rows.append(ft.Row([ft.Icon(ft.Icons.CHECK, size=12, color=T["accent_secondary"]), ft.Text(f"Keywords: {', '.join(keywords)}", size=12, color=T["text_secondary"])]))
    if sources_found:
        rows.append(ft.Row([ft.Icon(ft.Icons.CHECK, size=12, color=T["accent_secondary"]), ft.Text(f"Sources found: {sources_found}", size=12, color=T["text_secondary"])]))
    if crawl_status:
        rows.append(ft.Row([ft.Icon(ft.Icons.CHECK, size=12, color=T["accent_secondary"]), ft.Text(f"Crawl status: {crawl_status}", size=12, color=T["text_secondary"])]))
    if chunks_used:
        rows.append(ft.Row([ft.Icon(ft.Icons.CHECK, size=12, color=T["accent_secondary"]), ft.Text(f"Context chunks used: {', '.join(chunks_used)}", size=12, color=T["text_secondary"])]))
    if not rows:
        rows.append(ft.Text("No search performed for this response.", color=T["text_secondary"], size=12))

    return ft.ExpansionTile(
        title=ft.Text("Research & Scrape Steps", size=13, color=T["text_secondary"], font_family=config.FONT_FAMILY),
        leading=ft.Icon(ft.Icons.ACCOUNT_TREE_OUTLINED, size=16, color=T["accent_primary"]),
        controls=[ft.Container(content=ft.Column(rows, spacing=5, tight=True),
                                 padding=ft.padding.only(left=16, right=16, bottom=12))],
        bgcolor=ft.Colors.with_opacity(0.05, T["text_primary"]),
        collapsed_bgcolor=ft.Colors.with_opacity(0.02, T["text_primary"]),
        shape=ft.RoundedRectangleBorder(radius=10),
    )


def chunks_used_badge(chunks_used: list[str], on_click=None) -> ft.Container:
    count = len(chunks_used)
    label = f"{count} context chunk{'s' if count != 1 else ''} used"
    return ft.Container(
        content=ft.Row(
            [ft.Icon(ft.Icons.LAYERS_OUTLINED, size=12, color=T["accent_secondary"]),
             ft.Text(label, size=11, color=T["text_secondary"])],
            spacing=4, tight=True,
        ),
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
        border_radius=999,
        bgcolor=ft.Colors.with_opacity(0.2, T["accent_secondary"]),
        ink=True,
        on_click=on_click,
    )


# ---------------------------------------------------------------------------
# Message action bar
# ---------------------------------------------------------------------------
def message_action_bar(on_copy, on_regenerate, on_feedback_up=None, on_edit=None) -> ft.Row:
    actions = [
        ft.IconButton(icon=ft.Icons.CONTENT_COPY_OUTLINED, icon_size=15, icon_color=T["text_secondary"],
                       tooltip="Copy as Markdown", on_click=lambda e: on_copy()),
        ft.IconButton(icon=ft.Icons.REPLAY_ROUNDED, icon_size=15, icon_color=T["text_secondary"],
                       tooltip="Regenerate", on_click=lambda e: on_regenerate()),
    ]
    if on_feedback_up:
        actions.append(ft.IconButton(icon=ft.Icons.THUMB_UP_OUTLINED, icon_size=15,
                                       icon_color=T["text_secondary"], tooltip="Good response",
                                       on_click=lambda e: on_feedback_up()))
    if on_edit:
        actions.append(ft.IconButton(icon=ft.Icons.EDIT_OUTLINED, icon_size=15,
                                       icon_color=T["text_secondary"], tooltip="Edit and resend",
                                       on_click=lambda e: on_edit()))
    return ft.Row(actions, spacing=0, tight=True)


# ---------------------------------------------------------------------------
# Composite AI message block — sources -> reasoning -> markdown answer -> actions
# This is the main per-turn renderer main.py should use once a response is
# complete (ai_bubble above stays reserved for the live-streaming state).
# ---------------------------------------------------------------------------
def ai_message_block(text: str, sources: list[dict] = None, keywords: list[str] = None,
                      crawl_status: str = "", chunks_used: list[str] = None,
                      on_copy=None, on_regenerate=None, on_edit=None) -> ft.Container:
    components = []

    if sources:
        components.append(
            ft.Row(
                [
                    ft.Container(
                        width=20, height=20, border_radius=10,
                        gradient=ft.LinearGradient(colors=[T["accent_primary"], T["accent_highlight"]]),
                        content=ft.Icon(ft.Icons.AUTO_AWESOME, size=10, color="#FFFFFF"),
                        alignment=ft.alignment.center,
                    ),
                    ft.Text("Sources", size=13, weight=ft.FontWeight.BOLD, color=T["text_primary"]),
                ],
                spacing=8,
            )
        )
        components.append(citation_strip(sources))

    if keywords or crawl_status or chunks_used:
        components.append(thinking_accordion(keywords or [], len(sources or []), crawl_status, chunks_used))

    components.append(
        ft.Row(
            [
                ft.Container(
                    width=20, height=20, border_radius=10,
                    gradient=ft.LinearGradient(colors=[T["accent_primary"], T["accent_highlight"]]),
                    content=ft.Icon(ft.Icons.AUTO_AWESOME, size=10, color="#FFFFFF"),
                    alignment=ft.alignment.center,
                ),
                ft.Text("Answer", weight=ft.FontWeight.BOLD, size=13, color=T["text_primary"], font_family=config.FONT_FAMILY),
            ],
            spacing=8,
        )
    )
    components.append(
        ft.Markdown(
            text,
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            code_theme=ft.MarkdownCodeTheme.ATOM_ONE_DARK,
        )
    )

    components.append(
        message_action_bar(
            on_copy=on_copy or (lambda: None),
            on_regenerate=on_regenerate or (lambda: None),
            on_feedback_up=lambda: None,
            on_edit=on_edit,
        )
    )

    return ft.Container(
        content=ft.Column(components, spacing=12),
        padding=ft.padding.only(top=10, bottom=20, right=40),
        alignment=ft.alignment.center_left,
        animate_opacity=250,
    )


# ---------------------------------------------------------------------------
# Dynamic Live Response Block (Perplexity-Style Live Reasoning core)
# ---------------------------------------------------------------------------
class LiveResponseBlock(ft.Container):
    def __init__(self, on_copy, on_regenerate, on_edit=None):
        super().__init__(
            padding=ft.padding.only(top=10, bottom=20, right=40),
            alignment=ft.alignment.center_left,
            animate_opacity=250,
        )
        self.on_copy = on_copy
        self.on_regenerate = on_regenerate
        self.on_edit = on_edit

        # 1. Sources Header & Badges (hidden initially)
        self.sources_title = ft.Row(
            [
                ft.Container(
                    width=20, height=20, border_radius=10,
                    gradient=ft.LinearGradient(colors=[T["accent_primary"], T["accent_highlight"]]),
                    content=ft.Icon(ft.Icons.AUTO_AWESOME, size=10, color="#FFFFFF"),
                    alignment=ft.alignment.center,
                ),
                ft.Text("Sources", size=13, weight=ft.FontWeight.BOLD, color=T["text_primary"]),
            ],
            spacing=8,
            visible=False,
        )
        self.sources_strip_holder = ft.Container(visible=False)

        # 2. Steps Panel (loading indicator/spins, visible immediately)
        self.steps_list = ft.Column(spacing=5)
        self.steps_tile = ft.ExpansionTile(
            title=ft.Text("Research & Scrape Steps", size=13, color=T["text_secondary"], font_family=config.FONT_FAMILY),
            leading=ft.Icon(ft.Icons.ACCOUNT_TREE_OUTLINED, size=16, color=T["accent_primary"]),
            controls=[ft.Container(content=self.steps_list, padding=ft.padding.only(left=16, right=16, bottom=12))],
            bgcolor=ft.Colors.with_opacity(0.05, T["text_primary"]),
            collapsed_bgcolor=ft.Colors.with_opacity(0.02, T["text_primary"]),
            shape=ft.RoundedRectangleBorder(radius=10),
            initially_expanded=True,
            visible=True,
        )

        # 3. Answer Title & Output Streamer
        self.answer_title = ft.Row(
            [
                ft.Container(
                    width=20, height=20, border_radius=10,
                    gradient=ft.LinearGradient(colors=[T["accent_primary"], T["accent_highlight"]]),
                    content=ft.Icon(ft.Icons.AUTO_AWESOME, size=10, color="#FFFFFF"),
                    alignment=ft.alignment.center,
                ),
                ft.Text("Answer", weight=ft.FontWeight.BOLD, size=13, color=T["text_primary"], font_family=config.FONT_FAMILY),
            ],
            spacing=8,
        )
        self.answer_markdown = ft.Markdown(
            "Thinking...",
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            code_theme=ft.MarkdownCodeTheme.ATOM_ONE_DARK,
        )

        # 4. Action Row (hidden during streaming)
        self.actions_row = message_action_bar(on_copy, on_regenerate, on_feedback_up=lambda: None, on_edit=on_edit)
        self.actions_row.visible = False

        self.content = ft.Column(
            [
                self.sources_title,
                self.sources_strip_holder,
                self.steps_tile,
                self.answer_title,
                self.answer_markdown,
                self.actions_row,
            ],
            spacing=12,
        )

    def add_step(self, text: str, status: str = "running"):
        """
        status: "running" (pulsing ProgressRing), "done" (emerald checkmark), "pending" (grey dot)
        """
        found = False
        for c in self.steps_list.controls:
            if isinstance(c, ft.Row) and len(c.controls) > 1 and c.controls[1].value == text:
                # Update existing step status in place
                if status == "done":
                    c.controls[0] = ft.Icon(ft.Icons.CHECK, size=12, color=T["accent_secondary"])
                elif status == "running":
                    c.controls[0] = ft.ProgressRing(width=10, height=10, stroke_width=1.5, color=T["accent_primary"])
                found = True
                break
        
        if not found:
            if status == "done":
                indicator = ft.Icon(ft.Icons.CHECK, size=12, color=T["accent_secondary"])
            elif status == "running":
                indicator = ft.ProgressRing(width=10, height=10, stroke_width=1.5, color=T["accent_primary"])
            else:
                indicator = ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED_ROUNDED, size=12, color=T["text_secondary"])

            self.steps_list.controls.append(
                ft.Row(
                    [
                        indicator,
                        ft.Text(text, size=12.5, color=T["text_secondary"], font_family=config.FONT_FAMILY),
                    ],
                    spacing=8,
                )
            )
        self.update()

    def set_sources(self, sources: list[dict]):
        if sources:
            self.sources_title.visible = True
            self.sources_strip_holder.visible = True
            self.sources_strip_holder.content = citation_strip(sources)
            self.update()

    def set_answer(self, text: str):
        self.answer_markdown.value = text
        self.update()

    def finalize(self, text: str, related_questions: list[str] = None, on_related_click = None):
        self.answer_markdown.value = text
        # Collapse accordion on complete, matching sample_ui.py
        self.steps_tile.initially_expanded = False
        self.steps_tile.expanded = False
        self.actions_row.visible = True
        
        if related_questions:
            # Append related questions chip column at the end
            related_col = suggested_followups_row(related_questions, on_related_click)
            self.content.controls.append(related_col)

        self.update()


# ---------------------------------------------------------------------------
# Sidebar: thread list item
# ---------------------------------------------------------------------------
def session_list_item(title: str, updated_at: str, active: bool, on_click, on_delete) -> ft.Container:
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(
                    ft.Icons.CHAT_BUBBLE_OUTLINE, 
                    size=14, 
                    color=T["accent_primary"] if active else T["text_secondary"]
                ),
                ft.Text(
                    title, 
                    size=13, 
                    color=T["text_primary"] if active else T["text_secondary"], 
                    expand=True, 
                    max_lines=1, 
                    overflow=ft.TextOverflow.ELLIPSIS,
                    font_family=config.FONT_FAMILY
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE, 
                    icon_size=13,
                    icon_color=T["text_secondary"], 
                    on_click=lambda e: on_delete()
                ),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.all(10),
        border_radius=8,
        bgcolor=ft.Colors.with_opacity(0.12, T["accent_primary"]) if active else "transparent",
        ink=True,
        on_click=lambda e: on_click(),
    )


# ---------------------------------------------------------------------------
# Sidebar: Context Center toggle row
# ---------------------------------------------------------------------------
def context_toggle_row(filename: str, enabled: bool, on_change) -> ft.Row:
    return ft.Row(
        [
            ft.Text(filename, color=T["text_primary"], size=13, font_family=config.FONT_FAMILY,
                     expand=True, overflow=ft.TextOverflow.ELLIPSIS),
            ft.Switch(value=enabled, active_color=T["accent_primary"], on_change=on_change,
                       data=filename, scale=0.7),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )


# ---------------------------------------------------------------------------
# Sidebar: "This Chat's Files" toggle row (Section 5A.4) — per-thread .md
# files. Unlike global Context Center files (which live on disk and are
# managed outside the UI), session files are DB rows scoped to one thread,
# so each row also gets a delete button.
# ---------------------------------------------------------------------------
def session_context_toggle_row(file_id: int, filename: str, enabled: bool, on_change, on_delete) -> ft.Row:
    return ft.Row(
        [
            ft.Text(filename, color=T["text_primary"], size=13, font_family=config.FONT_FAMILY,
                     expand=True, overflow=ft.TextOverflow.ELLIPSIS),
            ft.Switch(value=enabled, active_color=T["accent_secondary"], on_change=on_change,
                       data=file_id, scale=0.7),
            ft.IconButton(icon=ft.Icons.CLOSE, icon_size=13, icon_color=T["text_secondary"],
                           tooltip="Remove from this thread", on_click=lambda e: on_delete(file_id)),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        spacing=0,
    )


# ---------------------------------------------------------------------------
# Sidebar: session stats card
# ---------------------------------------------------------------------------
def stats_card(keywords_generated: int, searches_performed: int,
               sources_found: int, pages_crawled: int) -> ft.Container:
    def stat_line(label: str, value: int) -> ft.Row:
        return ft.Row(
            [ft.Text(label, color=T["text_secondary"], size=12),
             ft.Text(str(value), color=T["text_primary"], size=12, weight=ft.FontWeight.BOLD)],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("Session Stats", color=T["text_primary"], size=13,
                         weight=ft.FontWeight.BOLD, font_family=config.FONT_FAMILY),
                stat_line("Keywords generated", keywords_generated),
                stat_line("Searches performed", searches_performed),
                stat_line("Sources found", sources_found),
                stat_line("Pages crawled", pages_crawled),
            ],
            spacing=8, tight=True,
        ),
        padding=14,
        border_radius=config.BORDER_RADIUS,
        bgcolor=ft.Colors.with_opacity(0.35, T["surface"]),
        border=ft.border.all(1, T["border"]),
    )


# ---------------------------------------------------------------------------
# Model dropdown
# ---------------------------------------------------------------------------
def model_dropdown(model_ids: list[str], selected: str, on_change) -> ft.Dropdown:
    return ft.Dropdown(
        value=selected if selected in model_ids else None,
        options=[ft.dropdown.Option(m) for m in model_ids],
        on_change=on_change,
        bgcolor=T["surface"],
        color=T["text_primary"],
        border_color="transparent",
        border_radius=999,
        text_size=12,
        dense=True,
        content_padding=ft.padding.symmetric(horizontal=12, vertical=6),
        hint_text="No models loaded" if not model_ids else "Select a model",
        width=170,
    )


# ---------------------------------------------------------------------------
# Connection status dot
# ---------------------------------------------------------------------------
def connection_status_dot(connected: bool) -> ft.Container:
    color = T["accent_secondary"] if connected else T["accent_highlight"]
    return ft.Container(width=8, height=8, border_radius=4, bgcolor=color,
                          tooltip="LM Studio connected" if connected else "LM Studio not running")


# ---------------------------------------------------------------------------
# Search mode toggle — rendered as a Perplexity "Pro Search"-style chip that
# cycles Auto -> Web -> Off -> URL on click, paired with a small popup menu
# for direct selection.
# ---------------------------------------------------------------------------
_MODE_LABELS = {
    config.SEARCH_MODE_AUTO: "Auto",
    config.SEARCH_MODE_FORCE_WEB: "Web Search",
    config.SEARCH_MODE_FORCE_NONE: "Search Off",
    config.SEARCH_MODE_URL_ONLY: "URL Only",
}


def search_mode_toggle(current_mode: str, on_change) -> ft.PopupMenuButton:
    return ft.PopupMenuButton(
        content=ft.Container(
            content=ft.Row(
                [ft.Icon(ft.Icons.TRAVEL_EXPLORE, size=12, color=T["accent_secondary"]),
                 ft.Text(_MODE_LABELS.get(current_mode, "Auto"), size=11, color=T["text_primary"], weight=ft.FontWeight.W_600)],
                spacing=5, tight=True,
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            border_radius=20,
            bgcolor=ft.Colors.with_opacity(0.1, T["accent_secondary"]),
        ),
        items=[
            ft.PopupMenuItem(text=label, on_click=lambda e, v=value: on_change(v))
            for value, label in _MODE_LABELS.items()
        ],
    )


# ---------------------------------------------------------------------------
# Settings dialog
# ---------------------------------------------------------------------------
def settings_dialog(base_url: str, embed_model: str, search_result_count: int,
                     ctx_token_budget: int, on_save) -> ft.AlertDialog:
    base_url_field = ft.TextField(label="LM Studio Base URL", value=base_url,
                                    bgcolor=T["surface"], color=T["text_primary"], border_color=T["border"])
    embed_model_field = ft.TextField(label="Embedding Model", value=embed_model,
                                       bgcolor=T["surface"], color=T["text_primary"], border_color=T["border"])
    search_count_field = ft.TextField(label="Search Result Count", value=str(search_result_count),
                                        bgcolor=T["surface"], color=T["text_primary"], border_color=T["border"],
                                        keyboard_type=ft.KeyboardType.NUMBER)
    ctx_budget_field = ft.TextField(label="Context Token Budget", value=str(ctx_token_budget),
                                      bgcolor=T["surface"], color=T["text_primary"], border_color=T["border"],
                                      keyboard_type=ft.KeyboardType.NUMBER)

    dialog = ft.AlertDialog(
        modal=True,
        bgcolor=T["surface"],
        shape=ft.RoundedRectangleBorder(radius=config.BORDER_RADIUS),
        title=ft.Text("Settings", color=T["text_primary"], font_family=config.FONT_FAMILY),
        content=ft.Column([base_url_field, embed_model_field, search_count_field, ctx_budget_field],
                            tight=True, spacing=12, width=320),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: e.page.close(dialog)),
            ft.FilledButton(
                "Save",
                style=ft.ButtonStyle(bgcolor=T["accent_primary"], shape=ft.RoundedRectangleBorder(radius=999)),
                on_click=lambda e: on_save(base_url_field.value, embed_model_field.value,
                                             search_count_field.value, ctx_budget_field.value, dialog),
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    return dialog


# ---------------------------------------------------------------------------
# Sidebar action buttons
# ---------------------------------------------------------------------------
def sidebar_action_button(label: str, icon, on_click, primary: bool = False) -> ft.Container:
    return ft.Container(
        content=ft.Row(
            [ft.Icon(icon, size=15, color=config.THEME_DARK["bg"] if primary else T["text_primary"]),
             ft.Text(label, size=12.5, color=config.THEME_DARK["bg"] if primary else T["text_primary"])],
            spacing=8, alignment=ft.MainAxisAlignment.CENTER,
        ),
        padding=ft.padding.symmetric(horizontal=14, vertical=9),
        border_radius=999,
        bgcolor=T["accent_primary"] if primary else ft.Colors.with_opacity(0.4, T["surface"]),
        border=None if primary else ft.border.all(1, T["border"]),
        ink=True,
        on_click=on_click,
        width=230 if primary else None,
    )


# ---------------------------------------------------------------------------
# Sidebar assembly — brand header, New Thread button, session list,
# Context Center toggles, This Chat's Files (Section 5A), stats card.
# main.py wires live data into this.
# ---------------------------------------------------------------------------
def build_sidebar(session_items: list, context_rows: list, session_file_rows: list, stats: dict,
                   on_new_chat, on_open_settings, on_add_session_file,
                   expanded: dict = None, on_toggle_expand=None,
                   collapsed: bool = False, on_toggle_collapse=None,
                   on_toggle_theme=None) -> ft.Container:
    """
    expanded: dict like {"recent": bool, "context": bool, "session_files": bool}
    controlling which collapsible sections start open.
    """
    if collapsed:
        return ft.Container(
            width=56,
            bgcolor=T["surface"],
            padding=ft.padding.symmetric(vertical=15),
            content=ft.Column(
                [
                    ft.Container(
                        width=28, height=28, border_radius=14,
                        gradient=ft.LinearGradient(colors=[T["accent_primary"], T["accent_highlight"]]),
                        content=ft.Icon(ft.Icons.AUTO_AWESOME, size=12, color="#FFFFFF"),
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(height=16),
                    ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT_ROUNDED, icon_color=T["text_secondary"],
                                   tooltip="Expand sidebar",
                                   on_click=(lambda e: on_toggle_collapse()) if on_toggle_collapse else None),
                    ft.Container(height=8),
                    ft.IconButton(icon=ft.Icons.ADD_CIRCLE_OUTLINE, icon_color=T["accent_primary"],
                                   tooltip="New Thread", on_click=on_new_chat),
                    ft.Container(expand=True),
                    ft.IconButton(icon=ft.Icons.SETTINGS_OUTLINED, icon_color=T["text_secondary"],
                                   tooltip="Settings", on_click=on_open_settings),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            ),
        )

    exp = expanded or {}

    def section(key: str, title: str, content_rows: list, default_open: bool = False) -> ft.ExpansionTile:
        return ft.ExpansionTile(
            title=ft.Text(title, size=10, color=T["text_secondary"], weight=ft.FontWeight.BOLD, font_family=config.FONT_FAMILY),
            initially_expanded=exp.get(key, default_open),
            controls=[ft.Container(content=ft.Column(content_rows, spacing=4), padding=ft.padding.only(top=6, bottom=6))],
            tile_padding=ft.padding.symmetric(horizontal=0),
            bgcolor=ft.Colors.TRANSPARENT,
            collapsed_bgcolor=ft.Colors.TRANSPARENT,
            icon_color=T["text_secondary"],
            collapsed_icon_color=T["text_secondary"],
            on_change=(lambda e, k=key: on_toggle_expand(k, e.data == "true")) if on_toggle_expand else None,
        )

    header = ft.Row(
        [
            ft.Container(
                width=28, height=28, border_radius=14,
                gradient=ft.LinearGradient(colors=[T["accent_primary"], T["accent_highlight"]]),
                content=ft.Icon(ft.Icons.AUTO_AWESOME, size=12, color="#FFFFFF"),
                alignment=ft.alignment.center,
            ),
            ft.Text("GAYATRI", size=16, weight=ft.FontWeight.BOLD, color=T["text_primary"], font_family=config.FONT_FAMILY),
            ft.Container(expand=True),
            ft.IconButton(icon=ft.Icons.CHEVRON_LEFT_ROUNDED, icon_size=18,
                           icon_color=T["text_secondary"], tooltip="Collapse sidebar",
                           on_click=(lambda e: on_toggle_collapse()) if on_toggle_collapse else None),
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    footer = ft.Row(
        [
            sidebar_action_button("Settings", ft.Icons.SETTINGS_OUTLINED, on_open_settings),
            ft.IconButton(
                icon=ft.Icons.LIGHT_MODE_OUTLINED if _current_theme.get("bg") == config.THEME_DARK["bg"] else ft.Icons.DARK_MODE_OUTLINED,
                icon_color=T["text_primary"],
                icon_size=16,
                on_click=on_toggle_theme,
                tooltip="Switch Theme Mode",
            )
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    recent_section = section(
        "recent", "THREADS",
        [ft.Column(session_items, spacing=4, scroll=ft.ScrollMode.AUTO, height=160)],
        default_open=True,
    )
    context_section = section("context", "CONTEXT CENTER", context_rows, default_open=False)
    session_files_section = section(
        "session_files", "THIS CHAT'S FILES",
        session_file_rows if session_file_rows else
        [ft.Text("No files added to this thread yet.", size=11, color=T["text_secondary"], italic=True)],
        default_open=False,
    )

    sidebar_content = [
        header,
        ft.Container(height=10),
        sidebar_action_button("New Thread", ft.Icons.ADD, on_new_chat, primary=True),
        ft.Container(height=10),
        recent_section,
        ft.Divider(height=1, color=T["border"]),
        context_section,
        ft.Divider(height=1, color=T["border"]),
        ft.Row(
            [
                ft.Container(expand=True, content=session_files_section),
                ft.IconButton(icon=ft.Icons.ADD_CIRCLE_OUTLINE, icon_size=14,
                               icon_color=T["accent_secondary"], tooltip="Add file to this thread only",
                               on_click=lambda e: on_add_session_file()),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            spacing=0,
        ),
        ft.Container(height=10),
        stats_card(stats.get("keywords_generated", 0), stats.get("searches_performed", 0),
                    stats.get("sources_found", 0), stats.get("pages_crawled", 0)),
        ft.Container(expand=True),
        footer,
    ]

    return ft.Container(
        width=config.SIDEBAR_WIDTH,
        bgcolor=T["surface"],
        padding=15,
        content=ft.Column(
            sidebar_content,
            spacing=10,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        ),
        border=ft.border.only(right=ft.border.BorderSide(1, T["border"])),
    )


# ---------------------------------------------------------------------------
# Bottom input dock — two rows: input line, then mode/model controls line
# ---------------------------------------------------------------------------
def input_dock(on_send, on_stop, on_attach, model_ids: list[str], selected_model: str,
               on_model_change, current_search_mode: str, on_search_mode_change,
               is_generating: bool = False, window_width: float = 1200) -> ft.Container:
    text_field = ft.TextField(
        hint_text="Ask anything, or paste a URL to analyze...",
        hint_style=ft.TextStyle(color=T["text_secondary"]),
        expand=True,
        border=ft.InputBorder.NONE,
        multiline=True, min_lines=1, max_lines=6,
        shift_enter=True,
        bgcolor="transparent", color=T["text_primary"], text_size=15,
    )

    send_button = ft.Container(
        content=ft.Icon(ft.Icons.STOP_ROUNDED if is_generating else ft.Icons.ARROW_UPWARD_ROUNDED,
                          size=15, color=config.THEME_DARK["bg"]),
        width=30, height=30, border_radius=15,
        bgcolor=T["accent_highlight"] if is_generating else T["accent_primary"],
        alignment=ft.alignment.center,
        ink=True,
        on_click=(lambda e: on_stop()) if is_generating else (lambda e: on_send(text_field.value)),
        animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
    )

    # Dynamic horizontal margins to adapt to screen width
    h_margin = 50 if window_width > 1200 else (30 if window_width > 1000 else 15)

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.IconButton(icon=ft.Icons.ADD_CIRCLE_OUTLINE, icon_color=T["text_secondary"],
                                       tooltip="Attach file", on_click=lambda e: on_attach()),
                        text_field,
                        send_button,
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        search_mode_toggle(current_search_mode, on_search_mode_change),
                        model_dropdown(model_ids, selected_model, on_model_change),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=6,
        ),
        padding=ft.padding.only(left=12, right=12, top=6, bottom=6),
        border_radius=22,
        bgcolor=ft.Colors.with_opacity(0.6, T["surface"]),
        border=ft.border.all(1, T["border"]),
        margin=ft.margin.only(bottom=20, left=h_margin, right=h_margin),
        shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.15, T["accent_primary"])),
    )