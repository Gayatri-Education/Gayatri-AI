"""
sample_ui.py — Interactive design sample for Gayatri AI
Acts as a frontend prototype demonstrating the 'Solar Aura / Eclipse Glass' theme.
Features: obsidian surfaces, glowing gradients, Light/Dark mode transitions, 
and compact Perplexity-style search indicators.
Run with: python sample_ui.py
"""

import flet as ft

# ---------------------------------------------------------------------------
# Design Tokens (Obsidian Dark & Dawn Light)
# ---------------------------------------------------------------------------
THEME = {
    "dark": {
        "bg": "#07090E",
        "surface": "#121622",
        "surface_card": "#181E2E",
        "border": "#1E2538",
        "accent": "#6C5CE7",          # Corona purple
        "accent_alt": "#FD79A8",      # Sunrise pink
        "accent_green": "#00B894",    # Emerald
        "text_primary": "#F8FAFC",
        "text_secondary": "#94A3B8",
    },
    "light": {
        "bg": "#F8FAFC",
        "surface": "#FFFFFF",
        "surface_card": "#F1F5F9",
        "border": "#E2E8F0",
        "accent": "#6C5CE7",          # Corona purple
        "accent_alt": "#D63031",      # Solar red
        "accent_green": "#0984E3",    # Clean blue
        "text_primary": "#0F172A",
        "text_secondary": "#475569",
    }
}

# Active design state
active_theme_mode = "dark"
active_theme = THEME[active_theme_mode]

def main(page: ft.Page):
    page.title = "Gayatri AI — Launch Look & Feel"
    page.bgcolor = active_theme["bg"]
    page.padding = 0
    page.window.min_width = 1000
    page.window.min_height = 700
    page.window.width = 1200
    page.window.height = 780
    page.window.center()

    # ---------------------------------------------------------------------------
    # Global References for Rebuilding / Theme Swapping
    # ---------------------------------------------------------------------------
    chat_list = ft.Column(expand=True, spacing=25, scroll=ft.ScrollMode.AUTO)
    sidebar_container = ft.Container(width=280)
    input_dock_container = ft.Container()
    chat_wrapper = ft.Container(expand=True, padding=ft.padding.symmetric(horizontal=60, vertical=20))
    top_bar = ft.Container(padding=ft.padding.symmetric(horizontal=30, vertical=15))

    # ---------------------------------------------------------------------------
    # Theme Toggler Action
    # ---------------------------------------------------------------------------
    def toggle_theme(e):
        global active_theme_mode, active_theme
        active_theme_mode = "light" if active_theme_mode == "dark" else "dark"
        active_theme = THEME[active_theme_mode]

        # Apply active colors
        page.bgcolor = active_theme["bg"]
        chat_wrapper.bgcolor = active_theme["bg"]
        
        # Redraw
        draw_top_bar()
        draw_sidebar()
        draw_chat_content()
        draw_input_dock()
        page.update()

    # ---------------------------------------------------------------------------
    # UI Component Rendering
    # ---------------------------------------------------------------------------
    def draw_top_bar():
        top_bar.content = ft.Row(
            [
                ft.Row(
                    [
                        ft.Container(
                            width=10, height=10, border_radius=5,
                            bgcolor=active_theme["accent_green"],
                        ),
                        ft.Text("SYSTEM ONLINE", size=10, color=active_theme["text_secondary"], weight=ft.FontWeight.BOLD),
                    ],
                    spacing=8,
                ),
                ft.Container(expand=True),
                ft.Text("Qwen 2.5 7B", size=11, color=active_theme["text_primary"], weight=ft.FontWeight.W_600),
            ]
        )

    def draw_sidebar():
        # Title and Logo
        header = ft.Row(
            [
                ft.Container(
                    width=28, height=28, border_radius=14,
                    gradient=ft.LinearGradient(
                        colors=[active_theme["accent"], active_theme["accent_alt"]],
                    ),
                    content=ft.Icon(ft.Icons.AUTO_AWESOME, size=14, color="#FFFFFF"),
                    alignment=ft.alignment.center,
                ),
                ft.Text("GAYATRI", size=16, weight=ft.FontWeight.BOLD, color=active_theme["text_primary"]),
            ],
            spacing=10,
        )

        # Thread List
        threads = [
            ("The Solar Corona Physics", True),
            ("Tailwind v4 vs CSS Variables", False),
            ("Flet Glassmorphic Cards Setup", False),
        ]
        thread_items = []
        for title, active in threads:
            thread_items.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE, size=14, color=active_theme["accent"] if active else active_theme["text_secondary"]),
                            ft.Text(title, size=13, color=active_theme["text_primary"] if active else active_theme["text_secondary"], expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ],
                        spacing=10,
                    ),
                    padding=ft.padding.all(10),
                    border_radius=8,
                    bgcolor=ft.Colors.with_opacity(0.12, active_theme["accent"]) if active else "transparent",
                    ink=True,
                )
            )

        # Context center switches
        context_files = ["project_context.md", "brand_voice.md"]
        context_items = []
        for fn in context_files:
            context_items.append(
                ft.Row(
                    [
                        ft.Text(fn, size=12.5, color=active_theme["text_primary"], expand=True),
                        ft.Switch(value=True, active_color=active_theme["accent"], scale=0.7),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )

        # Settings and Theme buttons
        footer = ft.Row(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.SETTINGS_OUTLINED, size=15, color=active_theme["text_primary"]),
                            ft.Text("Settings", size=13, color=active_theme["text_primary"]),
                        ],
                        spacing=8,
                    ),
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    border_radius=20,
                    bgcolor=ft.Colors.with_opacity(0.1, active_theme["text_primary"]),
                    ink=True,
                ),
                ft.IconButton(
                    icon=ft.Icons.LIGHT_MODE_OUTLINED if active_theme_mode == "dark" else ft.Icons.DARK_MODE_OUTLINED,
                    icon_color=active_theme["text_primary"],
                    icon_size=16,
                    on_click=toggle_theme,
                    tooltip="Switch Theme Mode",
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        sidebar_container.content = ft.Column(
            [
                header,
                ft.Container(height=15),
                ft.Text("THREADS", size=10, color=active_theme["text_secondary"], weight=ft.FontWeight.BOLD),
                ft.Column(thread_items, spacing=4),
                ft.Container(height=15),
                ft.Text("CONTEXT CENTER", size=10, color=active_theme["text_secondary"], weight=ft.FontWeight.BOLD),
                ft.Column(context_items, spacing=4),
                ft.Container(expand=True),
                footer,
            ],
            spacing=10,
        )
        sidebar_container.bgcolor = active_theme["surface"]
        sidebar_container.border = ft.border.only(right=ft.border.BorderSide(1, active_theme["border"]))
        sidebar_container.padding = 20

    def draw_chat_content():
        chat_list.controls.clear()

        # 1. User Message Block
        user_message = ft.Container(
            content=ft.Text(
                "Explain the solar corona physics, how warm does it get, and why?",
                size=15, color=THEME["dark"]["text_primary"],
            ),
            padding=15,
            border_radius=12,
            bgcolor=active_theme["accent"],
            alignment=ft.alignment.center_right,
            margin=ft.margin.only(left=80),
        )
        chat_list.controls.append(ft.Row([user_message], alignment=ft.MainAxisAlignment.END))

        # 2. Perplexity-Style AI Message Block
        # a) Sources Badge Grid
        sources_row = ft.Row(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(content=ft.Text("1", size=9, color="#FFFFFF", weight=ft.FontWeight.BOLD), width=14, height=14, border_radius=7, bgcolor=active_theme["accent_green"], alignment=ft.alignment.center),
                            ft.Text("nasa.gov", size=11, color=active_theme["text_primary"]),
                        ],
                        spacing=5, tight=True,
                    ),
                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                    border_radius=20,
                    bgcolor=ft.Colors.with_opacity(0.12, active_theme["text_primary"]),
                    border=ft.border.all(1, active_theme["border"]),
                ),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(content=ft.Text("2", size=9, color="#FFFFFF", weight=ft.FontWeight.BOLD), width=14, height=14, border_radius=7, bgcolor=active_theme["accent_green"], alignment=ft.alignment.center),
                            ft.Text("wikipedia.org", size=11, color=active_theme["text_primary"]),
                        ],
                        spacing=5, tight=True,
                    ),
                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                    border_radius=20,
                    bgcolor=ft.Colors.with_opacity(0.12, active_theme["text_primary"]),
                    border=ft.border.all(1, active_theme["border"]),
                ),
            ],
            spacing=8,
        )

        # b) Reasoning Timeline Panel
        reasoning_list = ft.Column(
            [
                ft.Row([ft.Icon(ft.Icons.CHECK, size=12, color=active_theme["accent_green"]), ft.Text("Keywords: solar corona heating mechanisms", size=12, color=active_theme["text_secondary"])]),
                ft.Row([ft.Icon(ft.Icons.CHECK, size=12, color=active_theme["accent_green"]), ft.Text("Queried NASA and Wikipedia archives (2 sources found)", size=12, color=active_theme["text_secondary"])]),
                ft.Row([ft.Icon(ft.Icons.CHECK, size=12, color=active_theme["accent_green"]), ft.Text("Parsed and semantically ranked context chunks (all clear)", size=12, color=active_theme["text_secondary"])]),
            ],
            spacing=5,
        )
        reasoning_panel = ft.ExpansionTile(
            title=ft.Text("Research & Scrape Steps", size=13, color=active_theme["text_secondary"]),
            leading=ft.Icon(ft.Icons.ACCOUNT_TREE_OUTLINED, size=16, color=active_theme["accent"]),
            controls=[ft.Container(content=reasoning_list, padding=ft.padding.only(left=16, right=16, bottom=12))],
            bgcolor=ft.Colors.with_opacity(0.05, active_theme["text_primary"]),
            collapsed_bgcolor=ft.Colors.with_opacity(0.02, active_theme["text_primary"]),
            shape=ft.RoundedRectangleBorder(radius=10),
        )

        # c) Answer Text
        answer_text = ft.Markdown(
            "The **solar corona** is the outermost layer of the Sun's atmosphere. "
            "Remarkably, it is much hotter than the Sun's visible surface (the photosphere). "
            "While the surface is about **5,500°C**, the corona reaches temperatures between "
            "**1,000,000°C and 3,000,000°C** [1].\n\n"
            "Physicists attribute this extreme temperature difference to two main mechanisms:\n"
            "*   **Magnetic Reconnection**: Solar magnetic field lines cross and release massive amounts of energy into the plasma.\n"
            "*   **Alfvén Waves**: Low-frequency electromagnetic waves carry energy upward from the convection zone [2].",
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
        )

        # d) Suggested Follow-ups
        followups = [
            "What are Alfvén waves in detail?",
            "How do satellites measure the corona's temperature?",
        ]
        followup_chips = []
        for q in followups:
            followup_chips.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.ADD, size=13, color=active_theme["accent"]),
                            ft.Text(q, size=12.5, color=active_theme["text_primary"]),
                        ],
                        spacing=8,
                    ),
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    border_radius=8,
                    border=ft.border.all(1, active_theme["border"]),
                    bgcolor=ft.Colors.with_opacity(0.04, active_theme["text_primary"]),
                    ink=True,
                )
            )

        ai_block = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                width=20, height=20, border_radius=10,
                                gradient=ft.LinearGradient(colors=[active_theme["accent"], active_theme["accent_alt"]]),
                                content=ft.Icon(ft.Icons.AUTO_AWESOME, size=10, color="#FFFFFF"),
                                alignment=ft.alignment.center,
                            ),
                            ft.Text("Sources", size=13, weight=ft.FontWeight.BOLD, color=active_theme["text_primary"]),
                        ],
                        spacing=8,
                    ),
                    sources_row,
                    ft.Container(height=5),
                    reasoning_panel,
                    answer_text,
                    ft.Container(height=10),
                    ft.Column(
                        [
                            ft.Text("Related Queries", size=11, color=active_theme["text_secondary"], weight=ft.FontWeight.BOLD),
                            ft.Column(followup_chips, spacing=6),
                        ],
                        spacing=8,
                    )
                ],
                spacing=12,
            ),
            padding=ft.padding.only(right=40),
        )
        chat_list.controls.append(ai_block)

    def draw_input_dock():
        text_field = ft.TextField(
            hint_text="Ask anything, or crawl a URL...",
            hint_style=ft.TextStyle(color=active_theme["text_secondary"]),
            expand=True,
            border=ft.InputBorder.NONE,
            bgcolor="transparent",
            color=active_theme["text_primary"],
            text_size=14,
        )

        send_button = ft.Container(
            content=ft.Icon(ft.Icons.ARROW_UPWARD_ROUNDED, size=15, color="#FFFFFF"),
            width=30, height=30, border_radius=15,
            bgcolor=active_theme["accent"],
            alignment=ft.alignment.center,
            ink=True,
        )

        mode_badge = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.TRAVEL_EXPLORE, size=12, color=active_theme["accent_green"]),
                    ft.Text("Pro Search: Auto", size=11, color=active_theme["text_primary"], weight=ft.FontWeight.W_600),
                ],
                spacing=5, tight=True,
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            border_radius=20,
            bgcolor=ft.Colors.with_opacity(0.1, active_theme["accent_green"]),
        )

        input_dock_container.content = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.IconButton(icon=ft.Icons.ADD_CIRCLE_OUTLINE, icon_color=active_theme["text_secondary"], icon_size=18),
                            text_field,
                            send_button,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        [
                            mode_badge,
                            ft.Text("Caps Lock for line break", size=10, color=active_theme["text_secondary"]),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    )
                ],
                spacing=5,
            ),
            padding=ft.padding.only(left=10, right=10, top=5, bottom=5),
            border_radius=16,
            bgcolor=active_theme["surface"],
            border=ft.border.all(1, active_theme["border"]),
            margin=ft.margin.only(bottom=20, left=40, right=40),
            shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.with_opacity(0.08, active_theme["accent"])),
        )

    # ---------------------------------------------------------------------------
    # Initial Assemblies
    # ---------------------------------------------------------------------------
    draw_top_bar()
    draw_sidebar()
    draw_chat_content()
    draw_input_dock()

    main_layout = ft.Column(
        [
            top_bar,
            chat_wrapper.content == chat_list or chat_wrapper,
            input_dock_container,
        ],
        expand=True,
        spacing=0,
    )
    chat_wrapper.content = chat_list

    page.add(
        ft.Row(
            [
                sidebar_container,
                ft.Container(content=main_layout, expand=True),
            ],
            expand=True,
            spacing=0,
        )
    )
    page.update()

if __name__ == "__main__":
    ft.app(target=main)
