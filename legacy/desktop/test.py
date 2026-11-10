import flet as ft

def main(page: ft.Page):
    # Window Configuration
    page.title = "Gayatri AI - Desktop Assistant"
    page.window_width = 980
    page.window_height = 680
    page.window_resizable = True
    page.bgcolor = "#0D0F12"  # Deep Obsidian Background
    page.padding = 0

    # Theme Configuration
    page.theme = ft.Theme(
        font_family="Inter",
        color_scheme=ft.ColorScheme(
            primary="#7C4DFF",      # Electric Violet
            secondary="#00E5FF",    # Tech Cyan
            surface="#161920",      # Dark Slate
        )
    )

    # --- LEFT SIDEBAR (Navigation) ---
    sidebar = ft.Container(
        content=ft.Column(
            [
                # App Branding / Logo placeholder
                ft.Container(
                    content=ft.Icon(name=ft.Icons.BOLT_ROUNDED, color="#7C4DFF", size=32),
                    margin=ft.margin.only(bottom=24),
                ),
                # Navigation Actions
                ft.IconButton(icon=ft.Icons.CHAT_BUBBLE_ROUNDED, icon_color="#E2E8F0", tooltip="Chat Workspace"),
                ft.IconButton(icon=ft.Icons.HISTORY_ROUNDED, icon_color="#94A3B8", tooltip="History"),
                ft.IconButton(icon=ft.Icons.MEMORY_ROUNDED, icon_color="#94A3B8", tooltip="Model Orchestrator"),
                ft.VerticalDivider(width=20, color="#161920"),
                ft.IconButton(icon=ft.Icons.SETTINGS_ROUNDED, icon_color="#94A3B8", tooltip="Settings"),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.START,
        ),
        width=68,
        bgcolor="#161920",  # Dark Slate
        padding=ft.padding.only(top=24, bottom=24),
    )

    # --- MAIN CONTENT AREA ---
    # Header Panel
    header = ft.Row(
        [
            ft.Column(
                [
                    ft.Text("Gayatri AI", size=20, weight=ft.FontWeight.BOLD, color="#E2E8F0"),
                    ft.Text("Local Inference Active (LM Studio)", size=11, color="#94A3B8", font_family="JetBrains Mono"),
                ],
                spacing=2
            ),
            # System Status Badges
            ft.Row(
                [
                    ft.Container(
                        content=ft.Text("⚡ 24.5 t/s", size=11, color="#00E5FF", font_family="JetBrains Mono"),
                        bgcolor="#1F2937",
                        padding=ft.padding.all(6),
                        border_radius=6,
                    ),
                    ft.Container(
                        content=ft.Text("MODEL: Llama-3-8B", size=11, color="#7C4DFF", font_family="JetBrains Mono"),
                        bgcolor="#1F2937",
                        padding=ft.padding.all(6),
                        border_radius=6,
                    ),
                ],
                spacing=8
            )
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    # Conversation Canvas
    chat_history = ft.ListView(
        expand=True,
        spacing=20,
        padding=ft.padding.only(top=10, bottom=10),
    )

    # Sample Conversation Stream for Look-and-Feel Demonstration
    chat_history.controls.append(
        ft.Row(
            [
                ft.Container(
                    content=ft.Text("User", size=11, color="#94A3B8", weight=ft.FontWeight.BOLD),
                    width=40,
                ),
                ft.Container(
                    content=ft.Text("How do I optimize local performance for embedded tasks?", color="#E2E8F0", size=14),
                    expand=True,
                )
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
    )

    chat_history.controls.append(
        ft.Row(
            [
                ft.Container(
                    content=ft.Icon(name=ft.Icons.AUTO_AWESOME_ROUNDED, color="#7C4DFF", size=18),
                    width=40,
                    alignment=ft.alignment.top_left,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Gayatri AI", size=11, color="#7C4DFF", weight=ft.FontWeight.BOLD),
                            ft.Text(
                                "To guarantee lightning-fast performance when operating offline via LM Studio, "
                                "consider offloading layers optimally to your GPU and adjusting context-window boundaries. "
                                "Here is a code framework blueprint for asynchronous generation:",
                                color="#E2E8F0",
                                size=14,
                            ),
                            # Code Block Mockup
                            ft.Container(
                                content=ft.Text(
                                    "import openai\n\n# Pointing directly to LM Studio local server architecture\n"
                                    "client = openai.OpenAI(base_url='http://localhost:1234/v1', api_key='lm-studio')",
                                    color="#00E5FF",
                                    font_family="JetBrains Mono",
                                    size=12,
                                ),
                                bgcolor="#0D0F12",
                                padding=14,
                                border_radius=8,
                                width=float("inf"),
                            )
                        ],
                        spacing=8,
                    ),
                    expand=True,
                )
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
    )

    # Input Command Bar Panel
    input_field = ft.TextField(
        hint_text="Ask Gayatri anything...",
        hint_style=ft.TextStyle(color="#94A3B8", size=14),
        border_color="#161920",
        focused_border_color="#7C4DFF",
        bgcolor="#161920",
        color="#E2E8F0",
        filled=True,
        expand=True,
        cursor_color="#7C4DFF",
        content_padding=16,
        border_radius=12,
    )

    input_container = ft.Row(
        [
            input_field,
            ft.IconButton(
                icon=ft.Icons.ARROW_UPWARD_ROUNDED,
                icon_color="#0D0F12",
                bgcolor="#7C4DFF",
                icon_size=20,
                width=48,
                height=48,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=12)
                )
            )
        ],
        spacing=12,
    )

    # Center Panel Construction
    workspace_panel = ft.Container(
        content=ft.Column(
            [
                header,
                ft.Divider(color="#161920", height=1),
                chat_history,
                input_container,
            ],
            expand=True,
            spacing=16,
        ),
        expand=True,
        padding=24,
    )

    # --- APPLICATION SHELL MOUNTING ---
    app_layout = ft.Row(
        [
            sidebar,
            workspace_panel
        ],
        expand=True,
        spacing=0,
    )

    page.add(app_layout)

if __name__ == "__main__":
    ft.app(target=main)