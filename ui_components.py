"""
ui_components.py — Gayatri AI v5.0
Reusable Flet widgets styled with the bespoke Terracotta & Deep Indigo Slate design system.
Maintains exact component layout & sections:
- Sources -> Research & Scrape steps -> Markdown answer -> Action bar
- Two-row bottom input dock (input row + mode/model selector row)
- Grouped sidebar (Header, New Thread, Threads, Context Center, This Chat's Files, Stats, Footer)
- Fully dynamic Dark/Light theme switching
"""

import flet as ft
import config
import db

# Dynamic theme routing to support Dark/Light mode on the fly
_current_theme = config.THEME_DARK

def set_active_theme(theme_colors: dict):
    global _current_theme
    _current_theme = theme_colors

class DynamicThemeDict(dict):
    def __getitem__(self, key):
        return _current_theme.get(key, config.THEME_DARK.get(key, "#FFFFFF"))
    def get(self, key, default=None):
        return _current_theme.get(key, config.THEME_DARK.get(key, default))
    def __contains__(self, key):
        return key in _current_theme or key in config.THEME_DARK

T = DynamicThemeDict()


# ---------------------------------------------------------------------------
# Sparkle avatar badge
# ---------------------------------------------------------------------------
def _sparkle_avatar(size: int = 22, icon_size: int = 11) -> ft.Container:
    return ft.Container(
        width=size,
        height=size,
        border_radius=size // 2,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[T["accent_primary"], T.get("accent_green", "#E16F41")],
        ),
        content=ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, size=icon_size, color="#FFFFFF"),
        alignment=ft.alignment.center,
        shadow=ft.BoxShadow(
            blur_radius=6,
            color=ft.Colors.with_opacity(0.3, T["accent_primary"]),
        ),
    )


# ---------------------------------------------------------------------------
# Empty-state welcome screen
# ---------------------------------------------------------------------------
def empty_state(on_suggestion_click=None) -> ft.Container:
    suggestions = [
        "Summarize a URL for me",
        "What's the latest news on AI?",
        "Explain a concept simply",
    ]

    suggestion_chips = [
        ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, size=13, color=T["accent_primary"]),
                    ft.Text(s, size=12.5, color=T["text_primary"], font_family=config.FONT_FAMILY, weight=ft.FontWeight.W_500),
                ],
                spacing=6,
                tight=True,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            border_radius=config.BORDER_RADIUS,
            bgcolor=T["surface"],
            border=ft.border.all(1, T["border"]),
            shadow=ft.BoxShadow(
                blur_radius=4,
                offset=ft.Offset(0, 1),
                color=ft.Colors.with_opacity(0.08, "#000000"),
            ),
            ink=True,
            on_click=(lambda e, q=s: on_suggestion_click(q)) if on_suggestion_click else None,
        )
        for s in suggestions
    ]

    res = ft.Container(
        content=ft.Column(
            [
                # Warm Terracotta Glowing Orb
                ft.Container(
                    width=60,
                    height=60,
                    border_radius=30,
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.top_left,
                        end=ft.alignment.bottom_right,
                        colors=[T["accent_primary"], T.get("accent_green", "#E16F41")],
                    ),
                    shadow=ft.BoxShadow(
                        blur_radius=20,
                        spread_radius=1,
                        color=ft.Colors.with_opacity(0.35, T["accent_primary"]),
                    ),
                    content=ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, size=28, color="#FFFFFF"),
                    alignment=ft.alignment.center,
                ),
                ft.Container(height=16),
                ft.Text(
                    "What can I help with?",
                    size=22,
                    weight=ft.FontWeight.BOLD,
                    color=T["text_primary"],
                    font_family=config.FONT_FAMILY,
                ),
                ft.Container(height=4),
                ft.Text(
                    "Ask a question, paste a URL to analyze, or attach context for this thread.",
                    size=13,
                    color=T["text_secondary"],
                    text_align=ft.TextAlign.CENTER,
                    font_family=config.FONT_FAMILY,
                ),
                ft.Container(height=22),
                ft.Row(
                    suggestion_chips,
                    wrap=True,
                    spacing=10,
                    run_spacing=10,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,
        expand=True,
        padding=40,
        data="empty_state",
    )
    res._is_empty_state = True
    return res


# ---------------------------------------------------------------------------
# Chat bubbles
# ---------------------------------------------------------------------------
def user_bubble(content: str) -> ft.Container:
    return ft.Container(
        content=ft.Text(
            content,
            size=14,
            color="#FFFFFF",
            font_family=config.FONT_FAMILY,
            selectable=True,
            no_wrap=False,
        ),
        padding=ft.padding.symmetric(horizontal=18, vertical=12),
        border_radius=ft.border_radius.only(
            top_left=config.BORDER_RADIUS,
            top_right=config.BORDER_RADIUS,
            bottom_left=config.BORDER_RADIUS,
            bottom_right=3,
        ),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[T["accent_primary"], "#E05D38"],
        ),
        shadow=ft.BoxShadow(
            blur_radius=8,
            offset=ft.Offset(0, 2),
            color=ft.Colors.with_opacity(0.25, T["accent_primary"]),
        ),
        margin=ft.margin.only(left=80, top=6, bottom=6, right=0),
        animate_opacity=200,
    )


def ai_bubble(content: str, streaming: bool = False) -> ft.Row:
    """Minimal AI turn — used for live-streaming placeholder before a response finishes."""
    bubble = ft.Container(
        content=ft.Text(
            content or ("Thinking..." if streaming else ""),
            color=T["text_primary"],
            size=14,
            font_family=config.FONT_FAMILY,
            selectable=True,
            no_wrap=False,
        ),
        padding=ft.padding.symmetric(horizontal=16, vertical=12),
        border_radius=config.BORDER_RADIUS,
        bgcolor=T["surface"],
        border=ft.border.all(1, T["border"]),
        shadow=ft.BoxShadow(
            blur_radius=4,
            offset=ft.Offset(0, 1),
            color=ft.Colors.with_opacity(0.08, "#000000"),
        ),
        expand=True,
        animate_opacity=200,
    )
    return ft.Row(
        [_sparkle_avatar(), bubble],
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.START,
        spacing=10,
    )


# ---------------------------------------------------------------------------
# Citation chips + source cards
# ---------------------------------------------------------------------------
def citation_chip(number: int, domain: str, on_click=None) -> ft.Container:
    return ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Text(
                        str(number),
                        size=9.5,
                        color="#FFFFFF",
                        weight=ft.FontWeight.BOLD,
                        font_family=config.FONT_MONO,
                    ),
                    width=16,
                    height=16,
                    border_radius=8,
                    bgcolor=T["accent_secondary"],
                    alignment=ft.alignment.center,
                ),
                ft.Text(
                    domain,
                    size=11.5,
                    weight=ft.FontWeight.W_500,
                    color=T["text_primary"],
                    font_family=config.FONT_FAMILY,
                ),
                ft.Icon(ft.Icons.NORTH_EAST_ROUNDED, size=10, color=T["text_secondary"]),
            ],
            spacing=6,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.symmetric(horizontal=10, vertical=5),
        border_radius=config.BORDER_RADIUS,
        bgcolor=ft.Colors.with_opacity(0.35, T.get("accent_subtle", T["surface"])),
        border=ft.border.all(1, T["border"]),
        shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.with_opacity(0.06, "#000000")),
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
# Follow-up suggestion chips
# ---------------------------------------------------------------------------
def suggested_followups_row(questions: list[str], on_select) -> ft.Column:
    if not questions:
        return ft.Column([])
    rows = [
        ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.AUTO_AWESOME_OUTLINED, size=13, color=T["accent_primary"]),
                    ft.Text(
                        q,
                        size=12.5,
                        color=T["text_primary"],
                        expand=True,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        font_family=config.FONT_FAMILY,
                    ),
                    ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, size=12, color=T["text_secondary"]),
                ],
                spacing=8,
            ),
            padding=ft.padding.symmetric(horizontal=14, vertical=9),
            border_radius=config.BORDER_RADIUS,
            border=ft.border.all(1, T["border"]),
            bgcolor=T.get("surface_muted", T["surface"]),
            ink=True,
            on_click=lambda e, question=q: on_select(question),
        )
        for q in questions
    ]
    return ft.Column(
        [
            ft.Row(
                [
                    ft.Icon(ft.Icons.EXPLORE_OUTLINED, size=13, color=T["accent_primary"]),
                    ft.Text("Related Queries", size=11.5, color=T["text_secondary"], weight=ft.FontWeight.BOLD, font_family=config.FONT_FAMILY),
                ],
                spacing=6,
            ),
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
        rows.append(
            ft.Row(
                [
                    ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, size=13, color=T["accent_primary"]),
                    ft.Text(f"Keywords: {', '.join(keywords)}", size=12, color=T["text_secondary"], font_family=config.FONT_FAMILY),
                ],
                spacing=8,
            )
        )
    if sources_found:
        rows.append(
            ft.Row(
                [
                    ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, size=13, color=T["accent_primary"]),
                    ft.Text(f"Sources found: {sources_found}", size=12, color=T["text_secondary"], font_family=config.FONT_FAMILY),
                ],
                spacing=8,
            )
        )
    if crawl_status:
        rows.append(
            ft.Row(
                [
                    ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, size=13, color=T["accent_primary"]),
                    ft.Text(f"Crawl status: {crawl_status}", size=12, color=T["text_secondary"], font_family=config.FONT_FAMILY),
                ],
                spacing=8,
            )
        )
    if chunks_used:
        rows.append(
            ft.Row(
                [
                    ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, size=13, color=T["accent_primary"]),
                    ft.Text(f"Context chunks used: {', '.join(chunks_used)}", size=12, color=T["text_secondary"], font_family=config.FONT_FAMILY),
                ],
                spacing=8,
            )
        )
    if not rows:
        rows.append(ft.Text("No search performed for this response.", color=T["text_secondary"], size=12, italic=True))

    return ft.ExpansionTile(
        title=ft.Row(
            [
                ft.Icon(ft.Icons.ACCOUNT_TREE_ROUNDED, size=14, color=T["accent_primary"]),
                ft.Text("Research & Scrape Steps", size=12.5, color=T["text_primary"], weight=ft.FontWeight.W_600, font_family=config.FONT_FAMILY),
            ],
            spacing=8,
        ),
        controls=[
            ft.Container(
                content=ft.Column(rows, spacing=6, tight=True),
                padding=ft.padding.only(left=26, right=16, bottom=12, top=4),
            )
        ],
        bgcolor=T.get("surface_muted", T["surface"]),
        collapsed_bgcolor=T.get("surface_muted", T["surface"]),
        shape=ft.RoundedRectangleBorder(radius=config.BORDER_RADIUS),
        collapsed_shape=ft.RoundedRectangleBorder(radius=config.BORDER_RADIUS),
        icon_color=T["text_secondary"],
        collapsed_icon_color=T["text_secondary"],
    )


def chunks_used_badge(chunks_used: list[str], on_click=None) -> ft.Container:
    count = len(chunks_used)
    label = f"{count} context chunk{'s' if count != 1 else ''} used"
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.LAYERS_OUTLINED, size=12, color=T["accent_secondary"]),
                ft.Text(label, size=11, color=T["text_primary"], font_family=config.FONT_FAMILY),
            ],
            spacing=4,
            tight=True,
        ),
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
        border_radius=config.BORDER_RADIUS,
        bgcolor=ft.Colors.with_opacity(0.2, T.get("accent_subtle", T["accent_secondary"])),
        border=ft.border.all(1, T["border"]),
        ink=True,
        on_click=on_click,
    )


# ---------------------------------------------------------------------------
# Message action bar
# ---------------------------------------------------------------------------
def message_action_bar(on_copy, on_regenerate, on_feedback_up=None, on_edit=None) -> ft.Row:
    actions = [
        ft.IconButton(
            icon=ft.Icons.CONTENT_COPY_ROUNDED,
            icon_size=15,
            icon_color=T["text_secondary"],
            tooltip="Copy as Markdown",
            on_click=lambda e: on_copy(),
        ),
        ft.IconButton(
            icon=ft.Icons.REFRESH_ROUNDED,
            icon_size=15,
            icon_color=T["text_secondary"],
            tooltip="Regenerate",
            on_click=lambda e: on_regenerate(),
        ),
    ]
    if on_feedback_up:
        actions.append(
            ft.IconButton(
                icon=ft.Icons.THUMB_UP_OUTLINED,
                icon_size=15,
                icon_color=T["text_secondary"],
                tooltip="Good response",
                on_click=lambda e: on_feedback_up(),
            )
        )
    if on_edit:
        actions.append(
            ft.IconButton(
                icon=ft.Icons.EDIT_OUTLINED,
                icon_size=15,
                icon_color=T["text_secondary"],
                tooltip="Edit and resend",
                on_click=lambda e: on_edit(),
            )
        )
    return ft.Row(actions, spacing=2, tight=True)


# ---------------------------------------------------------------------------
# Composite AI message block
# ---------------------------------------------------------------------------
def ai_message_block(text: str, sources: list[dict] = None, keywords: list[str] = None,
                      crawl_status: str = "", chunks_used: list[str] = None,
                      on_copy=None, on_regenerate=None, on_edit=None) -> ft.Container:
    components = []

    if sources:
        components.append(
            ft.Row(
                [
                    _sparkle_avatar(),
                    ft.Text("Sources", size=13, weight=ft.FontWeight.BOLD, color=T["text_primary"], font_family=config.FONT_FAMILY),
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
                _sparkle_avatar(),
                ft.Text("Answer", weight=ft.FontWeight.BOLD, size=13, color=T["text_primary"], font_family=config.FONT_FAMILY),
            ],
            spacing=8,
        )
    )
    is_light = _current_theme.get("bg") == config.THEME_LIGHT["bg"]
    components.append(
        ft.Markdown(
            text,
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            code_theme=ft.MarkdownCodeTheme.ATOM_ONE_LIGHT if is_light else ft.MarkdownCodeTheme.ATOM_ONE_DARK,
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
        padding=ft.padding.all(18),
        border_radius=config.BORDER_RADIUS,
        bgcolor=T["surface"],
        border=ft.border.all(1, T["border"]),
        shadow=ft.BoxShadow(
            blur_radius=6,
            offset=ft.Offset(0, 1),
            color=ft.Colors.with_opacity(0.08, "#000000"),
        ),
        margin=ft.margin.only(top=6, bottom=12, right=0),
        alignment=ft.alignment.center_left,
        animate_opacity=200,
    )


# ---------------------------------------------------------------------------
# Dynamic Live Response Block
# ---------------------------------------------------------------------------
class LiveResponseBlock(ft.Container):
    def __init__(self, on_copy, on_regenerate, on_edit=None):
        super().__init__(
            padding=ft.padding.all(18),
            border_radius=config.BORDER_RADIUS,
            bgcolor=T["surface"],
            border=ft.border.all(1, T["border"]),
            shadow=ft.BoxShadow(
                blur_radius=6,
                offset=ft.Offset(0, 1),
                color=ft.Colors.with_opacity(0.08, "#000000"),
            ),
            margin=ft.margin.only(top=6, bottom=12, right=0),
            alignment=ft.alignment.center_left,
            animate_opacity=200,
        )
        self.on_copy = on_copy
        self.on_regenerate = on_regenerate
        self.on_edit = on_edit

        # 1. Sources Header & Badges (hidden initially)
        self.sources_title = ft.Row(
            [
                _sparkle_avatar(),
                ft.Text("Sources", size=13, weight=ft.FontWeight.BOLD, color=T["text_primary"], font_family=config.FONT_FAMILY),
            ],
            spacing=8,
            visible=False,
        )
        self.sources_strip_holder = ft.Container(visible=False)

        # 2. Steps Panel (loading indicator/spins, visible ONLY when steps exist)
        self.steps_list = ft.Column(spacing=6)
        self.steps_tile = ft.ExpansionTile(
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.ACCOUNT_TREE_ROUNDED, size=14, color=T["accent_primary"]),
                    ft.Text("Research & Scrape Steps", size=12.5, color=T["text_primary"], weight=ft.FontWeight.W_600, font_family=config.FONT_FAMILY),
                ],
                spacing=8,
            ),
            controls=[
                ft.Container(
                    content=self.steps_list,
                    padding=ft.padding.only(left=26, right=16, bottom=12, top=4),
                )
            ],
            bgcolor=T.get("surface_muted", T["surface"]),
            collapsed_bgcolor=T.get("surface_muted", T["surface"]),
            shape=ft.RoundedRectangleBorder(radius=config.BORDER_RADIUS),
            collapsed_shape=ft.RoundedRectangleBorder(radius=config.BORDER_RADIUS),
            initially_expanded=True,
            visible=False,
            icon_color=T["text_secondary"],
            collapsed_icon_color=T["text_secondary"],
        )

        # 3. Answer Title & Output Streamer
        self.answer_title = ft.Row(
            [
                _sparkle_avatar(),
                ft.Text("Answer", weight=ft.FontWeight.BOLD, size=13, color=T["text_primary"], font_family=config.FONT_FAMILY),
            ],
            spacing=8,
        )
        is_light = _current_theme.get("bg") == config.THEME_LIGHT["bg"]
        self.answer_markdown = ft.Markdown(
            "Thinking...",
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            code_theme=ft.MarkdownCodeTheme.ATOM_ONE_LIGHT if is_light else ft.MarkdownCodeTheme.ATOM_ONE_DARK,
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
        self.steps_tile.visible = True
        found = False
        for c in self.steps_list.controls:
            if isinstance(c, ft.Row) and len(c.controls) > 1 and c.controls[1].value == text:
                if status == "done":
                    c.controls[0] = ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, size=13, color=T["accent_primary"])
                elif status == "running":
                    c.controls[0] = ft.ProgressRing(width=11, height=11, stroke_width=1.6, color=T["accent_primary"])
                found = True
                break
        
        if not found:
            if status == "done":
                indicator = ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, size=13, color=T["accent_primary"])
            elif status == "running":
                indicator = ft.ProgressRing(width=11, height=11, stroke_width=1.6, color=T["accent_primary"])
            else:
                indicator = ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED_ROUNDED, size=13, color=T["text_secondary"])

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
        self.steps_tile.initially_expanded = False
        self.steps_tile.expanded = False
        self.actions_row.visible = True
        
        if related_questions:
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
                    ft.Icons.CHAT_BUBBLE_ROUNDED if active else ft.Icons.CHAT_BUBBLE_OUTLINE_ROUNDED, 
                    size=14, 
                    color=T["accent_primary"] if active else T["text_secondary"]
                ),
                ft.Text(
                    title, 
                    size=13, 
                    color=T["text_primary"] if active else T["text_secondary"], 
                    weight=ft.FontWeight.W_600 if active else ft.FontWeight.W_400,
                    expand=True, 
                    max_lines=1, 
                    overflow=ft.TextOverflow.ELLIPSIS,
                    font_family=config.FONT_FAMILY,
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE_ROUNDED, 
                    icon_size=13,
                    icon_color=T["text_secondary"], 
                    tooltip="Delete thread",
                    on_click=lambda e: on_delete(),
                ),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.symmetric(horizontal=10, vertical=8),
        border_radius=config.BORDER_RADIUS,
        bgcolor=ft.Colors.with_opacity(0.15, T["accent_primary"]) if active else "transparent",
        border=ft.border.all(1, ft.Colors.with_opacity(0.25, T["accent_primary"])) if active else None,
        ink=True,
        on_click=lambda e: on_click(),
    )


# ---------------------------------------------------------------------------
# Sidebar: Context Center toggle row
# ---------------------------------------------------------------------------
def context_toggle_row(filename: str, enabled: bool, on_change) -> ft.Row:
    return ft.Row(
        [
            ft.Text(
                filename,
                color=T["text_primary"],
                size=12.5,
                font_family=config.FONT_FAMILY,
                expand=True,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
            ft.Switch(
                value=enabled,
                active_color=T["accent_primary"],
                on_change=on_change,
                data=filename,
                scale=0.7,
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )


# ---------------------------------------------------------------------------
# Sidebar: "This Chat's Files" toggle row
# ---------------------------------------------------------------------------
def session_context_toggle_row(file_id: int, filename: str, enabled: bool, on_change, on_delete) -> ft.Row:
    return ft.Row(
        [
            ft.Text(
                filename,
                color=T["text_primary"],
                size=12.5,
                font_family=config.FONT_FAMILY,
                expand=True,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
            ft.Switch(
                value=enabled,
                active_color=T["accent_primary"],
                on_change=on_change,
                data=file_id,
                scale=0.7,
            ),
            ft.IconButton(
                icon=ft.Icons.CLOSE_ROUNDED,
                icon_size=13,
                icon_color=T["text_secondary"],
                tooltip="Remove from this thread",
                on_click=lambda e: on_delete(file_id),
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        spacing=0,
    )


# ---------------------------------------------------------------------------
# Sidebar: session stats card
# ---------------------------------------------------------------------------
def stats_card(keywords_generated: int, searches_performed: int,
               sources_found: int, pages_crawled: int) -> ft.Container:
    def stat_line(label: str, value: int, color_str: str) -> ft.Row:
        return ft.Row(
            [
                ft.Text(label, color=T["text_secondary"], size=11.5, font_family=config.FONT_FAMILY),
                ft.Text(str(value), color=color_str, size=12, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.INSIGHTS_ROUNDED, size=13, color=T["accent_primary"]),
                        ft.Text("Session Stats", color=T["text_primary"], size=12.5,
                                weight=ft.FontWeight.BOLD, font_family=config.FONT_FAMILY),
                    ],
                    spacing=6,
                ),
                stat_line("Keywords generated", keywords_generated, T["accent_primary"]),
                stat_line("Searches performed", searches_performed, T.get("chart_1", "#85A6C7")),
                stat_line("Sources found", sources_found, T.get("accent_green", "#E16F41")),
                stat_line("Pages crawled", pages_crawled, T.get("accent_secondary", "#284167")),
            ],
            spacing=6,
            tight=True,
        ),
        padding=12,
        border_radius=config.BORDER_RADIUS,
        bgcolor=T.get("surface_muted", T["surface"]),
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
        border_radius=config.BORDER_RADIUS,
        text_size=11.5,
        dense=True,
        content_padding=ft.padding.symmetric(horizontal=12, vertical=5),
        hint_text="No models loaded" if not model_ids else "Select a model",
        hint_style=ft.TextStyle(color=T["text_secondary"], size=11),
        width=175,
    )


# ---------------------------------------------------------------------------
# Connection status dot
# ---------------------------------------------------------------------------
def connection_status_dot(connected: bool) -> ft.Container:
    color = T["accent_primary"] if connected else T["accent_highlight"]
    return ft.Container(
        width=8,
        height=8,
        border_radius=4,
        bgcolor=color,
        shadow=ft.BoxShadow(blur_radius=6, color=ft.Colors.with_opacity(0.4, color)),
        tooltip="LM Studio connected" if connected else "LM Studio not running",
    )


# ---------------------------------------------------------------------------
# Search mode toggle
# ---------------------------------------------------------------------------
_MODE_LABELS = {
    config.SEARCH_MODE_AUTO: "Auto",
    config.SEARCH_MODE_FORCE_WEB: "Web Search",
    config.SEARCH_MODE_AGENT: "Agent Mode 🤖",
    config.SEARCH_MODE_DEEP_RESEARCH: "Deep Research 🔬",
    config.SEARCH_MODE_URL_ONLY: "URL Only",
    config.SEARCH_MODE_FORCE_NONE: "Search Off",
}

_MODE_ICONS = {
    config.SEARCH_MODE_AUTO: ft.Icons.AUTO_AWESOME_ROUNDED,
    config.SEARCH_MODE_FORCE_WEB: ft.Icons.PUBLIC_ROUNDED,
    config.SEARCH_MODE_AGENT: ft.Icons.SMART_TOY_ROUNDED,
    config.SEARCH_MODE_DEEP_RESEARCH: ft.Icons.TRAVEL_EXPLORE_ROUNDED,
    config.SEARCH_MODE_URL_ONLY: ft.Icons.LINK_ROUNDED,
    config.SEARCH_MODE_FORCE_NONE: ft.Icons.OFFLINE_BOLT_ROUNDED,
}

def search_mode_toggle(current_mode: str, on_change) -> ft.PopupMenuButton:
    return ft.PopupMenuButton(
        content=ft.Container(
            content=ft.Row(
                [
                    ft.Icon(_MODE_ICONS.get(current_mode, ft.Icons.TRAVEL_EXPLORE), size=12, color=T["accent_primary"]),
                    ft.Text(_MODE_LABELS.get(current_mode, "Auto"), size=11, color=T["text_primary"], weight=ft.FontWeight.W_600, font_family=config.FONT_FAMILY),
                    ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN_ROUNDED, size=12, color=T["text_secondary"]),
                ],
                spacing=5,
                tight=True,
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            border_radius=config.BORDER_RADIUS,
            bgcolor=T.get("surface_muted", T["surface"]),
            border=ft.border.all(1, T["border"]),
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
    base_url_field = ft.TextField(
        label="LM Studio Base URL", value=base_url,
        bgcolor=T.get("surface_input", T["surface"]), color=T["text_primary"], border_color=T["border"],
        border_radius=config.BORDER_RADIUS, text_size=13,
    )
    embed_model_field = ft.TextField(
        label="Embedding Model", value=embed_model,
        bgcolor=T.get("surface_input", T["surface"]), color=T["text_primary"], border_color=T["border"],
        border_radius=config.BORDER_RADIUS, text_size=13,
    )
    search_count_field = ft.TextField(
        label="Search Result Count", value=str(search_result_count),
        bgcolor=T.get("surface_input", T["surface"]), color=T["text_primary"], border_color=T["border"],
        keyboard_type=ft.KeyboardType.NUMBER, border_radius=config.BORDER_RADIUS, text_size=13,
    )
    ctx_budget_field = ft.TextField(
        label="Context Token Budget", value=str(ctx_token_budget),
        bgcolor=T.get("surface_input", T["surface"]), color=T["text_primary"], border_color=T["border"],
        keyboard_type=ft.KeyboardType.NUMBER, border_radius=config.BORDER_RADIUS, text_size=13,
    )

    dialog = ft.AlertDialog(
        modal=True,
        bgcolor=T["surface"],
        shape=ft.RoundedRectangleBorder(radius=config.BORDER_RADIUS),
        title=ft.Text("Settings", color=T["text_primary"], font_family=config.FONT_FAMILY, weight=ft.FontWeight.BOLD),
        content=ft.Column(
            [base_url_field, embed_model_field, search_count_field, ctx_budget_field],
            tight=True, spacing=12, width=320,
        ),
        actions=[
            ft.TextButton(
                "Cancel",
                style=ft.ButtonStyle(color=T["text_secondary"]),
                on_click=lambda e: e.page.close(dialog),
            ),
            ft.Container(
                content=ft.Text("Save Changes", size=13, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                padding=ft.padding.symmetric(horizontal=18, vertical=10),
                border_radius=config.BORDER_RADIUS,
                bgcolor=T["accent_primary"],
                shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.3, T["accent_primary"])),
                ink=True,
                on_click=lambda e: on_save(
                    base_url_field.value, embed_model_field.value,
                    search_count_field.value, ctx_budget_field.value, dialog,
                ),
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    return dialog


# ---------------------------------------------------------------------------
# Memory Vault (Second Brain) Dialog & Item Cards
# ---------------------------------------------------------------------------
def memory_item_card(memory: dict, on_delete) -> ft.Container:
    category = memory.get("category", "fact").lower()
    cat_colors = {
        "preference": T["accent_secondary"],
        "project": T["accent_primary"],
        "fact": T.get("accent_green", "#E16F41"),
        "skill": T.get("chart_1", "#85A6C7"),
        "instruction": T["accent_highlight"],
    }
    cat_color = cat_colors.get(category, T["accent_primary"])

    return ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Text(category.upper(), size=9, weight=ft.FontWeight.BOLD, color="#FFFFFF", font_family=config.FONT_MONO),
                    padding=ft.padding.symmetric(horizontal=6, vertical=3),
                    border_radius=4,
                    bgcolor=cat_color,
                ),
                ft.Column(
                    [
                        ft.Text(memory.get("key", ""), size=12, weight=ft.FontWeight.BOLD, color=T["text_primary"], font_family=config.FONT_FAMILY),
                        ft.Text(memory.get("content", ""), size=11.5, color=T["text_secondary"], font_family=config.FONT_FAMILY),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                    icon_size=13,
                    icon_color=T["text_secondary"],
                    tooltip="Delete memory",
                    on_click=lambda e, mid=memory["id"]: on_delete(mid),
                ),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        border_radius=config.BORDER_RADIUS,
        bgcolor=T.get("surface_muted", T["surface"]),
        border=ft.border.all(1, T["border"]),
    )


def memory_vault_dialog(memories: list, on_add_memory, on_delete_memory, on_clear_all) -> ft.AlertDialog:
    key_field = ft.TextField(
        label="Key (e.g. user_tech_stack)",
        bgcolor=T.get("surface_input", T["surface"]),
        color=T["text_primary"],
        border_color=T["border"],
        border_radius=config.BORDER_RADIUS,
        text_size=12,
        dense=True,
    )
    content_field = ft.TextField(
        label="Memory Fact (e.g. Prefers Python and Flutter)",
        bgcolor=T.get("surface_input", T["surface"]),
        color=T["text_primary"],
        border_color=T["border"],
        border_radius=config.BORDER_RADIUS,
        text_size=12,
        multiline=True,
        min_lines=1,
        max_lines=3,
        dense=True,
    )
    cat_dropdown = ft.Dropdown(
        value="preference",
        options=[
            ft.dropdown.Option("preference", "Preference"),
            ft.dropdown.Option("project", "Project"),
            ft.dropdown.Option("fact", "Fact"),
            ft.dropdown.Option("skill", "Skill"),
            ft.dropdown.Option("instruction", "Instruction"),
        ],
        bgcolor=T.get("surface_input", T["surface"]),
        color=T["text_primary"],
        border_color=T["border"],
        border_radius=config.BORDER_RADIUS,
        text_size=12,
        dense=True,
    )

    items_column = ft.Column(
        [
            memory_item_card(m, on_delete=lambda mid: (on_delete_memory(mid), refresh_items()))
            for m in memories
        ] if memories else [
            ft.Container(
                content=ft.Text("No memories stored yet. Talk with Gayatri or add one below.", size=12, color=T["text_secondary"], italic=True),
                padding=20,
                alignment=ft.alignment.center,
            )
        ],
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
        height=220,
    )

    def refresh_items():
        all_m = db.list_memories()
        items_column.controls = [
            memory_item_card(m, on_delete=lambda mid: (on_delete_memory(mid), refresh_items()))
            for m in all_m
        ] if all_m else [
            ft.Container(
                content=ft.Text("No memories stored yet. Talk with Gayatri or add one below.", size=12, color=T["text_secondary"], italic=True),
                padding=20,
                alignment=ft.alignment.center,
            )
        ]
        items_column.update()

    def handle_add_click(e):
        k = (key_field.value or "").strip()
        c = (content_field.value or "").strip()
        cat = cat_dropdown.value or "fact"
        if k and c:
            on_add_memory(k, c, cat)
            key_field.value = ""
            content_field.value = ""
            key_field.update()
            content_field.update()
            refresh_items()

    dialog = ft.AlertDialog(
        modal=True,
        bgcolor=T["surface"],
        shape=ft.RoundedRectangleBorder(radius=config.BORDER_RADIUS),
        title=ft.Row(
            [
                ft.Icon(ft.Icons.PSYCHOLOGY_ROUNDED, color=T["accent_primary"], size=22),
                ft.Text("Second Brain — Memory Vault", color=T["text_primary"], font_family=config.FONT_FAMILY, weight=ft.FontWeight.BOLD, size=16),
            ],
            spacing=8,
        ),
        content=ft.Column(
            [
                ft.Text("Persistent knowledge and user preferences stored across sessions.", size=12, color=T["text_secondary"]),
                ft.Container(height=4),
                items_column,
                ft.Divider(height=1, color=T["border"]),
                ft.Text("Add Custom Memory", size=12.5, weight=ft.FontWeight.BOLD, color=T["text_primary"]),
                ft.Row([key_field, cat_dropdown], spacing=8),
                content_field,
                ft.Row(
                    [
                        ft.Container(expand=True),
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.ADD_ROUNDED, size=13, color="#FFFFFF"),
                                    ft.Text("Save Memory", size=12, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                                ],
                                spacing=4,
                                tight=True,
                            ),
                            padding=ft.padding.symmetric(horizontal=12, vertical=7),
                            border_radius=config.BORDER_RADIUS,
                            bgcolor=T["accent_primary"],
                            ink=True,
                            on_click=handle_add_click,
                        ),
                    ],
                ),
            ],
            tight=True,
            spacing=8,
            width=460,
        ),
        actions=[
            ft.TextButton(
                "Clear All Memories",
                style=ft.ButtonStyle(color=T["accent_highlight"]),
                on_click=lambda e: (on_clear_all(), refresh_items()),
            ),
            ft.TextButton(
                "Close",
                style=ft.ButtonStyle(color=T["text_secondary"]),
                on_click=lambda e: e.page.close(dialog),
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )
    return dialog


# ---------------------------------------------------------------------------
# Sidebar action buttons
# ---------------------------------------------------------------------------
def sidebar_action_button(label: str, icon, on_click, primary: bool = False, badge_text: str = None, expand: bool = False) -> ft.Container:
    if primary:
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, size=15, color="#FFFFFF"),
                    ft.Text(label, size=13, weight=ft.FontWeight.BOLD, color="#FFFFFF", font_family=config.FONT_FAMILY),
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=11),
            border_radius=config.BORDER_RADIUS,
            bgcolor=T["accent_primary"],
            shadow=ft.BoxShadow(
                blur_radius=8,
                offset=ft.Offset(0, 2),
                color=ft.Colors.with_opacity(0.25, T["accent_primary"]),
            ),
            ink=True,
            on_click=on_click,
            expand=expand,
            animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
        )

    row_controls = [
        ft.Icon(icon, size=14, color=T["text_secondary"]),
        ft.Text(label, size=12.5, color=T["text_primary"], font_family=config.FONT_FAMILY),
    ]
    if badge_text:
        row_controls.extend([
            ft.Container(expand=True),
            ft.Container(
                content=ft.Text(badge_text, size=9.5, weight=ft.FontWeight.BOLD, color="#FFFFFF", font_family=config.FONT_MONO),
                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                border_radius=8,
                bgcolor=T["accent_primary"],
            ),
        ])

    return ft.Container(
        content=ft.Row(
            row_controls,
            spacing=8,
            alignment=ft.MainAxisAlignment.START if badge_text else ft.MainAxisAlignment.CENTER,
        ),
        padding=ft.padding.symmetric(horizontal=14, vertical=8),
        border_radius=config.BORDER_RADIUS,
        bgcolor=T.get("surface_muted", T["surface"]),
        border=ft.border.all(1, T["border"]),
        ink=True,
        on_click=on_click,
        expand=expand,
    )


# ---------------------------------------------------------------------------
# Sidebar assembly
# ---------------------------------------------------------------------------
def build_sidebar(session_items: list, context_rows: list, session_file_rows: list, stats: dict,
                   on_new_chat, on_open_settings, on_add_session_file,
                   on_open_memory_vault=None, memory_count: int = 0,
                   expanded: dict = None, on_toggle_expand=None,
                   collapsed: bool = False, on_toggle_collapse=None,
                   on_toggle_theme=None) -> ft.Container:
    sidebar_bg = T.get("surface_sidebar", T["surface"])

    if collapsed:
        return ft.Container(
            width=56,
            bgcolor=sidebar_bg,
            padding=ft.padding.symmetric(vertical=16),
            content=ft.Column(
                [
                    _sparkle_avatar(28, 13),
                    ft.Container(height=16),
                    ft.IconButton(
                        icon=ft.Icons.CHEVRON_RIGHT_ROUNDED,
                        icon_color=T["text_secondary"],
                        tooltip="Expand sidebar",
                        on_click=(lambda e: on_toggle_collapse()) if on_toggle_collapse else None,
                    ),
                    ft.Container(height=8),
                    ft.Container(
                        content=ft.Icon(ft.Icons.ADD_ROUNDED, size=16, color="#FFFFFF"),
                        width=32, height=32, border_radius=config.BORDER_RADIUS,
                        bgcolor=T["accent_primary"],
                        alignment=ft.alignment.center,
                        ink=True,
                        tooltip="New Thread",
                        on_click=on_new_chat,
                    ),
                    ft.Container(height=8),
                    ft.IconButton(
                        icon=ft.Icons.PSYCHOLOGY_ROUNDED,
                        icon_color=T["accent_primary"],
                        tooltip="Memory Vault (Second Brain)",
                        on_click=on_open_memory_vault,
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.SETTINGS_OUTLINED,
                        icon_color=T["text_secondary"],
                        tooltip="Settings",
                        on_click=on_open_settings,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            ),
        )

    exp = expanded or {}

    def section(key: str, title: str, content_rows: list, default_open: bool = False) -> ft.ExpansionTile:
        return ft.ExpansionTile(
            title=ft.Text(title, size=10.5, color=T["text_secondary"], weight=ft.FontWeight.BOLD, font_family=config.FONT_FAMILY),
            initially_expanded=exp.get(key, default_open),
            controls=[
                ft.Container(
                    content=ft.Column(content_rows, spacing=4),
                    padding=ft.padding.only(top=4, bottom=6),
                )
            ],
            tile_padding=ft.padding.symmetric(horizontal=0),
            bgcolor=ft.Colors.TRANSPARENT,
            collapsed_bgcolor=ft.Colors.TRANSPARENT,
            icon_color=T["text_secondary"],
            collapsed_icon_color=T["text_secondary"],
            on_change=(lambda e, k=key: on_toggle_expand(k, e.data == "true")) if on_toggle_expand else None,
        )

    header = ft.Row(
        [
            _sparkle_avatar(26, 12),
            ft.Text("GAYATRI", size=16, weight=ft.FontWeight.BOLD, color=T["text_primary"], font_family=config.FONT_FAMILY),
            ft.Container(expand=True),
            ft.IconButton(
                icon=ft.Icons.CHEVRON_LEFT_ROUNDED,
                icon_size=18,
                icon_color=T["text_secondary"],
                tooltip="Collapse sidebar",
                on_click=(lambda e: on_toggle_collapse()) if on_toggle_collapse else None,
            ),
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    footer = ft.Row(
        [
            sidebar_action_button("Settings", ft.Icons.SETTINGS_OUTLINED, on_open_settings, expand=True),
            ft.IconButton(
                icon=ft.Icons.LIGHT_MODE_ROUNDED if _current_theme.get("bg") == config.THEME_DARK["bg"] else ft.Icons.DARK_MODE_ROUNDED,
                icon_color=T["text_primary"],
                icon_size=18,
                on_click=on_toggle_theme,
                tooltip="Switch Theme Mode",
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=8,
    )

    recent_section = section(
        "recent", "THREADS",
        session_items if session_items else [ft.Text("No chats yet.", size=11, color=T["text_secondary"], italic=True)],
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
        ft.Container(height=4),
        sidebar_action_button("New Thread", ft.Icons.ADD_ROUNDED, on_new_chat, primary=True),
        ft.Container(height=4),
        sidebar_action_button("Second Brain", ft.Icons.PSYCHOLOGY_ROUNDED, on_open_memory_vault, badge_text=f"{memory_count} mem"),
        ft.Container(height=6),
        recent_section,
        ft.Divider(height=1, color=T["border"]),
        context_section,
        ft.Divider(height=1, color=T["border"]),
        ft.Row(
            [
                ft.Container(expand=True, content=session_files_section),
                ft.IconButton(
                    icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                    icon_size=14,
                    icon_color=T["accent_primary"],
                    tooltip="Add file to this thread only",
                    on_click=lambda e: on_add_session_file() if on_add_session_file else None,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            spacing=0,
        ),
        ft.Container(height=8),
        stats_card(
            stats.get("keywords_generated", 0),
            stats.get("searches_performed", 0),
            stats.get("sources_found", 0),
            stats.get("pages_crawled", 0),
        ),
        ft.Container(expand=True),
        footer,
    ]

    return ft.Container(
        width=config.SIDEBAR_WIDTH,
        bgcolor=sidebar_bg,
        padding=15,
        content=ft.Column(
            sidebar_content,
            spacing=8,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        ),
        border=ft.border.only(right=ft.border.BorderSide(1, T["border"])),
    )


# ---------------------------------------------------------------------------
# Bottom input dock
# ---------------------------------------------------------------------------
def input_dock(on_send, on_stop, on_attach, model_ids: list[str], selected_model: str,
               on_model_change, current_search_mode: str, on_search_mode_change,
               is_generating: bool = False, window_width: float = 1200) -> ft.Container:
    def handle_submit(e=None):
        if is_generating:
            return
        val = (text_field.value or "").strip()
        if val:
            text_field.value = ""
            try:
                text_field.update()
            except Exception:
                pass
            on_send(val)

    text_field = ft.TextField(
        hint_text="Ask anything, or paste a URL to analyze...",
        hint_style=ft.TextStyle(color=T["text_secondary"], size=13.5),
        expand=True,
        border=ft.InputBorder.NONE,
        multiline=True,
        min_lines=1,
        max_lines=6,
        shift_enter=True,
        bgcolor="transparent",
        color=T["text_primary"],
        text_size=14.5,
        on_submit=handle_submit,
    )

    send_button = ft.Container(
        content=ft.Icon(
            ft.Icons.STOP_ROUNDED if is_generating else ft.Icons.ARROW_UPWARD_ROUNDED,
            size=15,
            color="#FFFFFF",
        ),
        width=32,
        height=32,
        border_radius=config.BORDER_RADIUS,
        bgcolor=T["accent_highlight"] if is_generating else T["accent_primary"],
        shadow=ft.BoxShadow(
            blur_radius=6,
            color=ft.Colors.with_opacity(0.3, T["accent_highlight"] if is_generating else T["accent_primary"]),
        ),
        alignment=ft.alignment.center,
        ink=True,
        on_click=(lambda e: on_stop()) if is_generating else (lambda e: handle_submit()),
        animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
    )

    # Dynamic horizontal margins to adapt to screen width
    h_margin = 50 if window_width > 1200 else (30 if window_width > 1000 else 15)

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                            icon_color=T["text_secondary"],
                            tooltip="Attach Markdown Context File",
                            on_click=lambda e: on_attach(),
                        ),
                        text_field,
                        send_button,
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        search_mode_toggle(current_mode=current_search_mode, on_change=on_search_mode_change),
                        model_dropdown(model_ids, selected_model, on_model_change),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=6,
        ),
        padding=ft.padding.only(left=12, right=12, top=6, bottom=6),
        border_radius=config.BORDER_RADIUS,
        bgcolor=T.get("surface_input", T["surface"]),
        border=ft.border.all(1, T["border"]),
        margin=ft.margin.only(bottom=20, left=h_margin, right=h_margin),
        shadow=ft.BoxShadow(
            blur_radius=8,
            offset=ft.Offset(0, 2),
            color=ft.Colors.with_opacity(0.1, "#000000"),
        ),
    )