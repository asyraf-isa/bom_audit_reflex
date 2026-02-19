import reflex as rx
from ..components.navbar import navbar
from ..bom_audit_reflex import AppState 

def render_generic_dialog(title, fields, on_submit, on_cancel, editing_mat_id, is_edit=False):
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
            rx.dialog.title(rx.cond(editing_mat_id != -1, f"Edit {title}", f"Add New {title}")),
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
            key=f"dialog-{editing_mat_id}", # Resets the form UI when editing_id changes
            max_width="450px",
        ),
    )

def materials_page() -> rx.Component:
    unit_options = ["pcs", "bottle", "meter", "kg", "liter", "sheet", "roll", "set", "box"]
    
    # This list defines what fields appear in the Material Dialog
    material_fields = [
        {"label": "Name", "name": "name", "type": "text", "default": AppState.mat_name},
        {"label": "Unit Cost (Cents)", "name": "cost", "type": "number", "default": AppState.mat_cost},
        {"label": "Unit", "name": "unit", "type": "select", "options": unit_options, "value": AppState.mat_unit, "on_change": AppState.set_mat_unit},
        {"label": "Supplier", "name": "supplier", "type": "text", "default": AppState.mat_supplier},
    ]

    return rx.vstack(
        navbar(),
        rx.vstack(
            rx.hstack(
                rx.heading("Materials Dashboard", size="8"),
                rx.spacer(),
                # Top "Add Material" Button
                render_generic_dialog("Material", material_fields, AppState.handle_material_submit, AppState.clear_mat_form, AppState.editing_mat_id, is_edit=False),
                width="100%", align="center", padding_bottom="2em",
            ),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("ID"), 
                        rx.table.column_header_cell("Name"),
                        rx.table.column_header_cell("Cost", justify="end"), 
                        rx.table.column_header_cell("Unit"),
                        rx.table.column_header_cell("Supplier"), 
                        rx.table.column_header_cell("Actions"), 
                    ),
                ),
                rx.table.body(
                    rx.foreach(
                        AppState.materials, 
                        lambda mat: rx.table.row(
                            rx.table.cell(mat[0]), 
                            rx.table.cell(mat[1], weight="bold"), 
                            rx.table.cell(
                                rx.vstack(
                                    rx.text(f"RM {mat[2].to(float) / 100:.2f}", weight="bold"),
                                    rx.text(f"{mat[2]} ¢", size="1", color_scheme="gray"),
                                    align_items="end", spacing="0", width="100%"
                                )
                            ),
                            rx.table.cell(mat[3]), 
                            rx.table.cell(rx.badge(mat[4], color_scheme="blue")),
                            rx.table.cell(
                                rx.hstack(
                                    # Edit Button
                                    rx.box(
                                        render_generic_dialog("Material", material_fields, AppState.handle_material_submit, AppState.clear_mat_form, AppState.editing_mat_id, is_edit=True),
                                        on_click=lambda: AppState.load_material_to_edit(mat)
                                    ),
                                    # Delete Button with Confirmation
                                    rx.alert_dialog.root(
                                        rx.alert_dialog.trigger(
                                            rx.button(rx.icon("trash-2"), color_scheme="red", variant="ghost", size="2")
                                        ),
                                        rx.alert_dialog.content(
                                            rx.alert_dialog.title("Delete Material"),
                                            rx.alert_dialog.description(f"Are you sure you want to delete {mat[1]}?"),
                                            rx.hstack(
                                                rx.alert_dialog.cancel(rx.button("Cancel", variant="soft", color_scheme="gray")),
                                                rx.alert_dialog.action(
                                                    rx.button("Delete", color_scheme="red", on_click=lambda: AppState.delete_material(mat[0]))
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
        on_mount=AppState.get_materials 
    )