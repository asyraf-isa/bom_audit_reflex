import reflex as rx
from ..components.navbar import navbar
# Import your AppState from the main file
from ..bom_audit_reflex import AppState 

def products_page() -> rx.Component:
    return rx.vstack(
        navbar(),
        rx.heading("Products Dashboard", size="8"),
        rx.button("Refresh Products", on_click=AppState.get_products),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("ID"),
                    rx.table.column_header_cell("Product Name"),
                    rx.table.column_header_cell("Selling Price"),
                    rx.table.column_header_cell("Labor"),
                    rx.table.column_header_cell("Overhead"),
                ),
            ),
            rx.table.body(
                rx.foreach(AppState.products, lambda prod: rx.table.row(
                    rx.table.cell(prod[0]), rx.table.cell(prod[1]), 
                    rx.table.cell(prod[2]), rx.table.cell(prod[3]), 
                    rx.table.cell(prod[4])
                ))
            ),
            width="100%",
            padding="2em",
        ),
        on_mount=AppState.get_products
    )