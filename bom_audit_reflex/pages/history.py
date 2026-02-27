import reflex as rx
from ..components.navbar import navbar
# Import your AppState from the main file
from ..bom_audit_reflex import AppState 

def history_page() -> rx.Component:
    return rx.vstack(
        navbar(),
        rx.container(
            rx.heading("Material Price History", size="7"),
            rx.recharts.line_chart(
                # DYNAMIC LINES: This creates one line per material
                rx.foreach(
                    AppState.material_names,
                    lambda m: rx.recharts.line(
                        data_key=m,
                        type="stepAfter",
                        name=m,
                        # Optional: Use a function to assign different colors
                        stroke="#8884d8", 
                        connect_nulls=True,
                    )
                ),
                rx.recharts.x_axis(data_key="date"),
                rx.recharts.y_axis(),
                rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                rx.recharts.tooltip(),
                rx.recharts.legend(),
                data=AppState.chart_material_history,
                width="100%",
                height=400,
            ),
            width="100%",
        ),
        on_mount=AppState.load_all
    )