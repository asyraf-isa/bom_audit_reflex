import reflex as rx
from ..components.navbar import navbar
from ..bom_audit_reflex import AppState 

def render_generic_dialog(title, fields, on_submit, on_cancel, editing_recipe_id, is_edit=False):
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
                    value=field.get("value"),
                    on_change=field.get("on_change"),
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
            rx.dialog.title(rx.cond(editing_recipe_id != -1, f"Edit {title}", f"Add New {title}")),
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
            key=f"dialog-{editing_recipe_id}", # Resets the form UI when editing_id changes
            max_width="450px",
        ),
    )

def recipes_page() -> rx.Component:
    
    # This list defines what fields appear in the Material Dialog
    recipe_fields = [
        {
            "label": "Material to Assign", 
            "name": "material_name", 
            "type": "select", 
            "options": AppState.material_options, # The list of names
            "value": AppState.recipe_mname, 
            "on_change": AppState.set_material_selection # Updates the ID in background
        },
        {
            "label": "Quantity", 
            "name": "recipe_quantity", 
            "type": "number", 
            "default": AppState.recipe_rquantity
        },
        {
            "label": "For Product", 
            "name": "product_name", 
            "type": "select", 
            "options": AppState.product_options, # The list of names
            "value": AppState.recipe_pname, 
            "on_change": AppState.set_product_selection # Updates the ID in background
        },
    ]

    return rx.vstack(
        navbar(),
        rx.vstack(
            rx.hstack(
                rx.heading("Product Recipe Lookup", size="8"),
                rx.spacer(),
                # Top "Add Recipe" Button
                render_generic_dialog("Recipe", recipe_fields, AppState.handle_recipe_submit, AppState.clear_recipe_form, AppState.editing_recipe_id, is_edit=False),
                width="100%", align="center", padding_bottom="2em",
            ),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Product Name"), 
                        rx.table.column_header_cell("Material Name"),
                        rx.table.column_header_cell("Quantity"), 
                        rx.table.column_header_cell("Cost", justify="end"),
                        rx.table.column_header_cell("Supplier"), 
                        rx.table.column_header_cell("Actions"), 
                    ),
                ),
                rx.table.body(
                    rx.foreach(
                        AppState.recipes, 
                        lambda recipe: rx.table.row(
                            rx.table.cell(recipe[1], weight="bold"), 
                            rx.table.cell(recipe[2]), 
                            rx.table.cell(rx.text(f"{recipe[3]} {recipe[5]}")), 
                            rx.table.cell(rx.badge(f"RM {recipe[4].to(float) / 100:.2f}/{recipe[5]}", color_scheme="green"), justify="end"), 
                            rx.table.cell(rx.badge(recipe[6], color_scheme="blue")),
                            rx.table.cell(
                                rx.hstack(
                                    # Edit Button
                                    rx.box(
                                        render_generic_dialog("Recipe", recipe_fields, AppState.handle_recipe_submit, AppState.clear_recipe_form, AppState.editing_recipe_id, is_edit=True),
                                        on_click=lambda: AppState.load_recipe_to_edit(recipe)
                                    ),
                                    # Delete Button with Confirmation
                                    rx.alert_dialog.root(
                                        rx.alert_dialog.trigger(
                                            rx.button(rx.icon("trash-2"), color_scheme="red", variant="ghost", size="2")
                                        ),
                                        rx.alert_dialog.content(
                                            rx.alert_dialog.title("Delete Recipe"),
                                            rx.alert_dialog.description(f"Are you sure you want to delete {recipe[2]} from {recipe[1]}?"),
                                            rx.hstack(
                                                rx.alert_dialog.cancel(rx.button("Cancel", variant="soft", color_scheme="gray")),
                                                rx.alert_dialog.action(
                                                    rx.button("Delete", color_scheme="red", on_click=lambda: AppState.delete_recipe(recipe[0]))
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