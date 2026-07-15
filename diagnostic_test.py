"""
diagnostic_test.py — bisection test to isolate the gray-box rendering issue.
Mirrors main.py's exact container/layout nesting but with static dummy
content instead of ListView/Markdown/PopupMenuButton, to determine whether
the bug is structural (Row/Column/Container nesting) or widget-specific
(ListView, Markdown, PopupMenuButton, Dropdown).
Run: python diagnostic_test.py
"""

import flet as ft

BG = "#0B0F19"
SURFACE = "#1A1F2E"
BORDER = "#2A2F3E"
TEXT = "#F5F6FA"


def main(page: ft.Page):
    page.title = "Diagnostic Test"
    page.bgcolor = BG
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0

    # Sidebar — same fixed-width pattern as main.py
    sidebar = ft.Container(width=280, bgcolor=SURFACE, content=ft.Text("SIDEBAR", color=TEXT))

    # Step 1: plain solid-color container, no ListView, no Column nesting
    step1_content = ft.Container(expand=True, bgcolor="#FF00FF", content=ft.Text("STEP 1: solid magenta box", color=TEXT))

    # Step 2: Container > Column(expand) > Container(expand, solid color) — same nesting as main_area
    step2_inner = ft.Container(expand=True, bgcolor="#00FF00", content=ft.Text("STEP 2: green inside Column", color="#000000"))
    step2_content = ft.Container(
        expand=True, bgcolor=BG,
        content=ft.Column([ft.Text("top bar placeholder", color=TEXT), step2_inner], expand=True, spacing=0),
    )

    # Step 3: same as step 2 but swap the colored box for an actual empty ft.ListView
    step3_listview = ft.ListView(expand=True)
    step3_wrapper = ft.Container(content=step3_listview, expand=True, bgcolor="#00FFFF")
    step3_content = ft.Container(
        expand=True, bgcolor=BG,
        content=ft.Column([ft.Text("top bar placeholder", color=TEXT), step3_wrapper], expand=True, spacing=0),
    )

    current_step = ft.Container(expand=True, content=step1_content)

    def show_step(step_content):
        current_step.content = step_content
        page.update()

    controls_bar = ft.Row(
        [
            ft.ElevatedButton("Step 1: solid color", on_click=lambda e: show_step(step1_content)),
            ft.ElevatedButton("Step 2: nested Column", on_click=lambda e: show_step(step2_content)),
            ft.ElevatedButton("Step 3: with ListView", on_click=lambda e: show_step(step3_content)),
        ]
    )

    page.add(
        ft.Column(
            [
                ft.Container(content=controls_bar, padding=10, bgcolor=SURFACE),
                ft.Row([sidebar, current_step], expand=True, spacing=0),
            ],
            expand=True,
            spacing=0,
        )
    )


if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)
