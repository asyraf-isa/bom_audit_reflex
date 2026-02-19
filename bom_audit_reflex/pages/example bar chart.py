import reflex as rx
from ..components.navbar import navbar
# Import your AppState from the main file
from ..bom_audit_reflex import AppState 

def reports_page() -> rx.Component:
    data = [
        {"name": "Page A", "uv": 4000, "pv": 2400},
        {"name": "Page B", "uv": 3000, "pv": 1398},
        {"name": "Page C", "uv": 2000, "pv": 9800},
        {"name": "Page D", "uv": 2780, "pv": 3908},
        {"name": "Page E", "uv": 1890, "pv": 4800},
        {"name": "Page F", "uv": 2390, "pv": 3800},
        {"name": "Page G", "uv": 3490, "pv": 4300},
    ]

    return rx.vstack(
        navbar(),
        rx.container(
            rx.recharts.bar_chart(
                # Order matters: Axes and Grid first
                rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                rx.recharts.x_axis(data_key="name"),
                rx.recharts.y_axis(),
                rx.recharts.tooltip(),
                rx.recharts.legend(),
                # The actual Bars
                rx.recharts.bar(
                    data_key="uv",
                    stroke=rx.color("accent", 9),
                    fill=rx.color("accent", 8),
                ),
                rx.recharts.bar(
                    data_key="pv",
                    stroke=rx.color("green", 9),
                    fill=rx.color("green", 8),
                ),
                data=data,
                width="100%",
                height=300, # Increased height for visibility
            ),
            width="100%",
            padding="2em",
        ),
        width="100%",
    )

###########################

class AppState(rx.State):
    reports: list[list] = []

    @rx.var
    def chart_data(self) -> list[dict]:
        # Transforms [name, price, cost...] into {"name": "...", "uv": ...}
        return [
            {"name": row[0], "uv": row[1], "pv": row[2]} 
            for row in self.reports
        ]
    
rx.recharts.bar_chart(
    rx.recharts.bar(data_key="uv", fill="#8884d8"), # Price
    rx.recharts.bar(data_key="pv", fill="#82ca9d"), # Cost
    rx.recharts.x_axis(data_key="name"),
    data=AppState.chart_data,
    width="100%",
    height=300,
)