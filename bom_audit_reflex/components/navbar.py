import reflex as rx

def navbar_icons_item(text: str, icon: str, url: str) -> rx.Component:
    return rx.link(
        rx.hstack(rx.icon(icon), rx.text(text, size="4", weight="medium")), href=url
    )


def navbar_icons_menu_item(text: str, icon: str, url: str) -> rx.Component:
    return rx.link(
        rx.hstack(rx.icon(icon, size=16), rx.text(text, size="3", weight="medium")),
        href=url,
    )


def navbar() -> rx.Component:
    return rx.box(
        rx.color_mode.button(position="bottom-left"),
        rx.desktop_only(
            rx.hstack(
                rx.hstack(
                    rx.image(
                        src="/logo.png",
                        width="2.25em",
                        height="auto",
                        border_radius="25%",
                    ),
                    rx.heading("SmartBOM Audit", size="7", weight="bold"),
                    align_items="center",
                ),
                rx.hstack(
                    navbar_icons_item("Materials", "pencil_ruler", "/#"),
                    navbar_icons_item("Products", "factory", "/products"),
                    navbar_icons_item("Recipe", "blocks", "/recipes"),
                    navbar_icons_item("Report", "chart_no_axes_combined", "/reports"),
                    navbar_icons_item("History", "circle_dollar_sign", "/history"),
                    spacing="6",
                ),
                justify="between",
                align_items="center",
            ),
        ),
        rx.mobile_and_tablet(
            rx.hstack(
                rx.hstack(
                    rx.image(
                        src="/logo.png", width="2em", height="auto", border_radius="25%"
                    ),
                    rx.heading("SmartBOM Audit", size="6", weight="bold"),
                    align_items="center",
                ),
                rx.menu.root(
                    rx.menu.trigger(rx.icon("menu", size=30)),
                    rx.menu.content(
                        navbar_icons_menu_item("Materials", "pencil_ruler", "/#"),
                        navbar_icons_menu_item("Products", "factory", "/products"),
                        navbar_icons_menu_item("Recipe", "blocks", "/recipes"),
                        navbar_icons_menu_item("Report", "chart_no_axes_combined", "/reports"),
                        navbar_icons_menu_item("History", "circle_dollar_sign", "/history"),
                    ),
                    justify="end",
                ),
                justify="between",
                align_items="center",
            ),
        ),
        bg=rx.color("accent", 3),
        padding="1em",
        # position="fixed",
        # top="0px",
        # z_index="5",
        width="100%",
    )