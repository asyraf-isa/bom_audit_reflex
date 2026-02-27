import reflex as rx
from ..components.navbar import navbar
from ..bom_audit_reflex import AppState 

def render_generic_dialog(title, fields, on_submit, on_cancel, editing_prod_id, is_edit=False):
    """
    Bulletproof Generic Dialog:
    Uses .get() for every field access to prevent KeyErrors during compilation.
    """
    def render_field(field):
        return rx.vstack(
            rx.text(field.get("label", ""), size="2", weight="bold"),
            rx.cond(
                field.get("type") == "select",
                # Render Dropdown
                rx.select(
                    field.get("options", []),
                    name=field.get("name", ""),
                    value=field.get("value", ""),
                    on_change=field.get("on_change", []),
                    width="100%",
                    required=True,
                ),
                # Render Text/Number Input
                rx.input(
                    name=field.get("name", ""),
                    type_=field.get("type", "text"),
                    default_value=field.get("default", ""),
                    width="100%",
                    required=True,
                ),
            ),
            width="100%", align_items="start",
        )

    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button(
                rx.icon("pencil" if is_edit else "plus"), 
                f"{'Edit' if is_edit else 'Add'} {title}",
                on_click=on_cancel if not is_edit else [],
                variant="solid" if not is_edit else "ghost",
                color_scheme="blue" if not is_edit else "gray",
            )
        ),
        rx.dialog.content(
            rx.dialog.title(rx.cond(editing_prod_id != -1, f"Edit {title}", f"Add New {title}")),
            rx.form(
                rx.vstack(
                    *[render_field(f) for f in fields],
                    spacing="4",
                ),
                rx.hstack(
                    rx.dialog.close(rx.button("Cancel", type="button", variant="soft", color_scheme="gray", on_click=on_cancel)),
                    rx.dialog.close(rx.button("Save Changes", type="submit")),
                    padding_top="1.5em", justify="end",
                ),
                on_submit=on_submit,
            ),
            key=f"dialog-{editing_prod_id}", # Resets the form UI when editing_id changes
            max_width="450px",
        ),
    )

def products_page() -> rx.Component:
    # not use unit_options = ["pcs", "bottle", "meter", "kg", "liter", "sheet", "roll", "set", "box"]
    
    # This list defines what fields appear in the Product Dialog
    product_fields = [
        {"label": "Name", "name": "name", "type": "text", "default": AppState.prod_name},
        {"label": "Selling Price (Cents)", "name": "selling_price", "type": "number", "default": AppState.prod_selling_price},
        #{"label": "Unit", "name": "unit", "type": "select", "options": unit_options, "value": AppState.mat_unit, "on_change": AppState.set_mat_unit},
        {"label": "Labor Cost (Cents)", "name": "labor_cost", "type": "number", "default": AppState.prod_labor_cost},
        {"label": "Overhead Cost (Cents)", "name": "overhead_cost", "type": "number", "default": AppState.prod_overhead_cost},
    ]

    return rx.vstack(
        navbar(),
        rx.vstack(
            rx.hstack(
                rx.heading("Products Dashboard", size="8"),
                rx.spacer(),
                # Top "Add Product" Button
                render_generic_dialog("Product", product_fields, AppState.handle_product_submit, AppState.clear_product_form, AppState.editing_prod_id, is_edit=False),
                width="100%", align="center", padding_bottom="2em",
            ),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("ID"), 
                        rx.table.column_header_cell("Product Name"),
                        rx.table.column_header_cell("Selling Price", justify="end"), 
                        rx.table.column_header_cell("Labor Cost", justify="end"),
                        rx.table.column_header_cell("Overhead Cost", justify="end"), 
                        rx.table.column_header_cell("Actions"), 
                    ),
                ),
                rx.table.body(
                    rx.foreach(
                        AppState.products, 
                        lambda prod: rx.table.row(
                            rx.table.cell(prod[0]), 
                            rx.table.cell(prod[1], weight="bold"), 
                            rx.table.cell(
                                rx.vstack(
                                    rx.text(f"RM {prod[2].to(float) / 100:.2f}", weight="bold"),
                                    rx.text(f"{prod[2]} ¢", size="1", color_scheme="gray"),
                                    align_items="end", spacing="0", width="100%"
                                )
                            ),
                            rx.table.cell(
                                rx.vstack(
                                    rx.text(f"RM {prod[3].to(float) / 100:.2f}", weight="bold"),
                                    rx.text(f"{prod[3]} ¢", size="1", color_scheme="gray"),
                                    align_items="end", spacing="0", width="100%"
                                )
                            ),
                            rx.table.cell(
                                rx.vstack(
                                    rx.text(f"RM {prod[4].to(float) / 100:.2f}", weight="bold"),
                                    rx.text(f"{prod[4]} ¢", size="1", color_scheme="gray"),
                                    align_items="end", spacing="0", width="100%"
                                )
                            ),
                            rx.table.cell(
                                rx.hstack(
                                    # Edit Button
                                    rx.box(
                                        render_generic_dialog("Product", product_fields, AppState.handle_product_submit, AppState.clear_product_form, AppState.editing_prod_id, is_edit=True),
                                        on_click=lambda: AppState.load_product_to_edit(prod)
                                    ),
                                    # Delete Button with Confirmation
                                    rx.alert_dialog.root(
                                        rx.alert_dialog.trigger(
                                            rx.button(rx.icon("trash-2"), color_scheme="red", variant="ghost", size="2")
                                        ),
                                        rx.alert_dialog.content(
                                            rx.alert_dialog.title("Delete Product"),
                                            rx.alert_dialog.description(f"Are you sure you want to delete {prod[1]}?"),
                                            rx.hstack(
                                                rx.alert_dialog.cancel(rx.button("Cancel", variant="soft", color_scheme="gray")),
                                                rx.alert_dialog.action(
                                                    rx.button("Delete", color_scheme="red", on_click=lambda: AppState.delete_product(prod[0]))
                                                ),
                                                justify="end", spacing="3",
                                            ),
                                        ),
                                    ),
                                    spacing="2",
                                )
                            ),
                        )
                    )
                ),
                width="100%", variant="surface",
            ),
            padding_x="4em", width="100%", max_width="1250px",
        ),
        on_mount=AppState.load_all
    )