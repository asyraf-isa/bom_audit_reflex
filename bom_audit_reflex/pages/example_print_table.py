## Simple Table

import reflex as rx

data = [
    [23, "John Smith", "Tailor"],
    [27, "Rose Will", "Nurse"],
    [31, "Mike Brown", "Teacher"],
]

def table_example():
    return rx.table(
        rx.thead(
            rx.tr(
                rx.th("Age"),
                rx.th("Name"),
                rx.th("Profession"),
            )
        ),
        rx.tbody(
            *[
                rx.tr(
                    rx.td(row[0]),
                    rx.td(row[1]),
                    rx.td(row[2]),
                )
                for row in data
            ]
        ),
        width="100%",
    )

app = rx.App()
app.add_page(table_example)


# Dynamic Table (Recommended)
import reflex as rx

class TableState(rx.State):
    data = [
        [23, "John Smith", "Tailor"],
        [27, "Rose Will", "Nurse"],
        [31, "Mike Brown", "Teacher"],
    ]

def table_example():
    return rx.table(
        rx.thead(
            rx.tr(
                rx.th("Age"),
                rx.th("Name"),
                rx.th("Profession"),
            )
        ),
        rx.tbody(
            rx.foreach(
                TableState.data,
                lambda row: rx.tr(
                    rx.td(row[0]),
                    rx.td(row[1]),
                    rx.td(row[2]),
                ),
            )
        ),
        width="100%",
    )

app = rx.App()
app.add_page(table_example)


# The best using dictionary

class TableState(rx.State):
    data = [
        {"age": 23, "name": "John Smith", "job": "Tailor"},
        {"age": 27, "name": "Rose Will", "job": "Nurse"},
    ]

def table_example():
    return rx.table(
        rx.thead(
            rx.tr(
                rx.th("Age"),
                rx.th("Name"),
                rx.th("Profession"),
            )
        ),
        rx.tbody(
            rx.foreach(
                TableState.data,
                lambda row: rx.tr(
                    rx.td(row["age"]),
                    rx.td(row["name"]),
                    rx.td(row["job"]),
                ),
            )
        ),
    )






# | Simple Table      | Dynamic Table        |
# | ----------------- | -------------------- |
# | Static data       | Reactive state       |
# | No auto-update    | Auto-update          |
# | Basic Python loop | `rx.foreach()`       |
# | For display only  | For interactive apps |




import reflex as rx

def index():
    return rx.vstack(
        # Button to trigger the state function
        rx.button("Generate Report", on_click=AppState.get_reports),
        
        # Displaying the results
        rx.cond(
            AppState.reports,
            rx.table.root(
                rx.table.body(
                    rx.foreach(
                        AppState.reports,
                        lambda row: rx.table.row(
                            rx.table.cell(row[0]), # Name
                            rx.table.cell(row[1]), # Price
                            rx.table.cell(row[2]), # Cost
                            rx.table.cell(row[3]), # Profit
                            rx.table.cell(row[4]), # Margin
                        )
                    )
                )
            ),
            rx.text("No data available. Click Generate.")
        )
    )