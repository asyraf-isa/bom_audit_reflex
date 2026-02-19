import reflex as rx
from ..components.navbar import navbar
# Import your AppState from the main file
from ..bom_audit_reflex import AppState 

def reports_page() -> rx.Component:
    return rx.vstack(
        navbar(),
        # 1. Chart Section
        rx.container(
            rx.recharts.bar_chart(
                rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                rx.recharts.x_axis(data_key="Product"),
                rx.recharts.y_axis(),
                rx.recharts.tooltip(),
                rx.recharts.legend(),
                rx.recharts.bar(
                    data_key="Selling Price (RM)",
                    stroke=rx.color("accent", 9),
                    fill=rx.color("accent", 8),
                ),
                rx.recharts.bar(
                    data_key="Profit (RM)",
                    stroke=rx.color("green", 9),
                    fill=rx.color("green", 8),
                ),
                data=AppState.chart_data,
                width="100%",
                height=300,
            ),
            width="100%",
        ),

        rx.center(  # <--- force centering
            rx.container(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Product Name"), 
                            rx.table.column_header_cell("Selling Price", justify="end"),
                            rx.table.column_header_cell("Production Cost", justify="end"), 
                            rx.table.column_header_cell("Material Cost", justify="end"), 
                            rx.table.column_header_cell("Profit", justify="end"),
                            rx.table.column_header_cell("Margin (%)", justify="center"), 
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            AppState.reports,
                            lambda report: rx.table.row(
                                rx.table.cell(report[0]),
                                # Selling Price
                                rx.table.cell(
                                    rx.vstack(
                                        rx.text(f"RM {report[1].to(float) / 100:.2f}", weight="bold"),
                                        rx.text(f"{report[1]} ¢", size="1", color_scheme="gray"),
                                        align_items="end", width="100%", spacing="0",
                                    )
                                ),
                                # Production Cost
                                rx.table.cell(
                                    rx.vstack(
                                        rx.text(f"RM {report[2].to(float) / 100:.2f}", weight="bold"),
                                        rx.text(f"{report[2]} ¢", size="1", color_scheme="gray"),
                                        align_items="end", width="100%", spacing="0",
                                    )
                                ),
                                # Material Cost
                                rx.table.cell(
                                    rx.vstack(
                                        rx.text(f"RM {report[3].to(float) / 100:.2f}", weight="bold"),
                                        rx.text(f"{report[3]} ¢", size="1", color_scheme="gray"),
                                        align_items="end", width="100%", spacing="0",
                                    )
                                ),
                                # Profit
                                rx.table.cell(
                                    rx.vstack(
                                        rx.text(f"RM {report[4].to(float) / 100:.2f}", weight="bold"),
                                        rx.text(f"{report[4]} ¢", size="1", color_scheme="gray"),
                                        align_items="end", width="100%", spacing="0",
                                    )
                                ),
                                rx.table.cell(
                                    rx.vstack(
                                        # rx.cond(
                                        #     report[4].to(float) < 20,
                                        #     rx.badge(rx.icon("triangle_alert"), rx.text(f"{report[4].to(float):.2f} %"), color_scheme="red", size="2"),
                                        #     rx.badge(rx.icon("check_check"), rx.text(f"{report[4].to(float):.2f} %"), color_scheme="green", size="2"),
                                        # ),
                                        rx.match(
                                            True,
                                            (report[5].to(float) > 15, rx.badge(rx.icon("check_check"), rx.text(f"{report[5].to(float):.2f} %"), color_scheme="green", size="2")),
                                            (report[5].to(float) > 0, rx.badge(rx.icon("triangle_alert"), rx.text(f"{report[5].to(float):.2f} %"), color_scheme="yellow", size="2")),
                                            rx.badge(rx.icon("power_off"), rx.text(f"{report[5].to(float):.2f} %"), color_scheme="red", size="2"),
                                        ),
                                        width="100%", spacing="0",
                                    )
                                ),
                            )
                        )
                    ),
                    width="100%",
                    variant="surface",
                ),
                max_width="1250px", 
            ),
            width="100%", # Ensures rx.center takes up full width
        ),
        padding_bottom="5em",
        on_mount=AppState.get_reports
    )