import reflex as rx
from .bom_db_manager import DatabaseManager

# Initialize the manager
db = DatabaseManager()

class AppState(rx.State):
    # --- State Variables ---
    materials: list[list] = [] 
    products: list[list] = [] 
    recipes: list[list] = [] 
    reports: list[list] = [] 
    material_history: list[list] = []

    # --- Connection Resilience Logic ---
    def run_db_query(self, query_func, *args, **kwargs):
        """
        Wraps database calls to catch stale connections common in cloud/serverless environments.
        If a call fails, it disposes of the pool so the next attempt starts fresh.
        """
        try:
            return query_func(*args, **kwargs)
        except Exception as e:
            print(f"DATABASE ERROR: {e}")
            # Clear the pool to force reconnection on the next try
            db.engine.dispose()
            raise e

    def load_all(self):
        """
        Entry point for page loads. Retries once if the initial connection is stale.
        """
        max_retries = 2
        for attempt in range(max_retries):
            try:
                self.get_materials()
                self.get_products()
                self.get_material_history()
                self.get_reports()
                
                if self.filter_product_name == "All Products":
                    self.get_all_recipes()
                else:
                    self.set_filter_and_load(self.filter_product_name)
                return # Success
            except Exception:
                if attempt == max_retries - 1:
                    return rx.toast.error("Database connection lost. Please refresh the page.")
                print(f"Connection stale, retrying... (Attempt {attempt + 1})")

    # --- Material Methods ---
    mat_name: str = ""
    mat_cost: str = ""
    mat_unit: str = ""
    mat_supplier: str = ""
    editing_mat_id: int = -1

    def set_mat_unit(self, val: str): self.mat_unit = val

    def load_material_to_edit(self, mat: list):
        self.editing_mat_id = int(mat[0])
        self.mat_name = str(mat[1])
        self.mat_cost = str(mat[2])
        self.mat_unit = str(mat[3])
        self.mat_supplier = str(mat[4])

    def clear_material_form(self):
        self.editing_mat_id = -1
        self.mat_name = ""
        self.mat_cost = ""
        self.mat_unit = ""
        self.mat_supplier = ""

    def handle_material_submit(self, form_data: dict):
        self.mat_name = form_data.get("name", "")
        self.mat_cost = form_data.get("cost", "")
        self.mat_unit = form_data.get("unit", self.mat_unit)
        self.mat_supplier = form_data.get("supplier", "")
        return self.save_material()

    def save_material(self):
        try:
            cost_val = int(self.mat_cost) if self.mat_cost else 0
        except ValueError:
            return rx.toast.error("Cost must be a whole number (cents).")
        
        try:
            if self.editing_mat_id == -1:
                success, msg = self.run_db_query(db.insert_material, self.mat_name, cost_val, self.mat_unit, self.mat_supplier)
            else:
                success, msg = self.run_db_query(db.update_material, self.editing_mat_id, self.mat_name, cost_val, self.mat_unit, self.mat_supplier)
            
            if success:
                self.get_materials()
                self.clear_material_form()
                return rx.toast.success(msg)
            return rx.toast.error(msg)
        except Exception as e:
            return rx.toast.error(f"Save failed: {str(e)}")

    def delete_material(self, mat_id: int):
        try:
            success, msg = self.run_db_query(db.delete_material, mat_id)
            if success:
                self.get_materials()
                return rx.toast.success(msg)
            return rx.toast.error(msg)
        except Exception as e:
            return rx.toast.error(f"Delete failed: {str(e)}")

    def get_materials(self):
        try:
            raw_mat = self.run_db_query(db.get_materials)
            self.materials = [list(mat) for mat in raw_mat] if raw_mat else []
        except Exception:
            self.materials = []

    # --- Product Methods ---
    prod_name: str = ""
    prod_selling_price: str = ""
    prod_labor_cost: str = ""
    prod_overhead_cost: str = ""
    editing_prod_id: int = -1

    def load_product_to_edit(self, prod: list):
        self.editing_prod_id = int(prod[0])
        self.prod_name = str(prod[1])
        self.prod_selling_price = str(prod[2])
        self.prod_labor_cost = str(prod[3])
        self.prod_overhead_cost = str(prod[4])

    def clear_product_form(self):
        self.editing_prod_id = -1
        self.prod_name = ""
        self.prod_selling_price = ""
        self.prod_labor_cost = ""
        self.prod_overhead_cost = ""

    def handle_product_submit(self, form_data: dict):
        self.prod_name = form_data.get("name", "")
        self.prod_selling_price = form_data.get("selling_price", "")
        self.prod_labor_cost = form_data.get("labor_cost", "")
        self.prod_overhead_cost = form_data.get("overhead_cost", "")
        return self.save_product()

    def save_product(self):
        try:
            int_sp = int(self.prod_selling_price) if self.prod_selling_price else 0
            int_lc = int(self.prod_labor_cost) if self.prod_labor_cost else 0
            int_oc = int(self.prod_overhead_cost) if self.prod_overhead_cost else 0
        except ValueError:
            return rx.toast.error("Prices and costs must be whole numbers (cents).")
        
        try:
            if self.editing_prod_id == -1:
                success, msg = self.run_db_query(db.insert_product, self.prod_name, int_sp, int_lc, int_oc)
            else:
                success, msg = self.run_db_query(db.update_product, self.editing_prod_id, self.prod_name, int_sp, int_lc, int_oc)
            
            if success:
                self.get_products()
                self.clear_product_form()
                return rx.toast.success(msg)
            return rx.toast.error(msg)
        except Exception as e:
            return rx.toast.error(f"Product save failed: {str(e)}")

    def delete_product(self, prod_id: int):
        try:
            success, msg = self.run_db_query(db.delete_product, prod_id)
            if success:
                self.get_products()
                return rx.toast.success(msg)
            return rx.toast.error(msg)
        except Exception as e:
            return rx.toast.error(f"Delete failed: {str(e)}")
    
    def get_products(self):
        try:
            raw_products = self.run_db_query(db.get_products)
            self.products = [list(prod) for prod in raw_products] if raw_products else []
        except Exception:
            self.products = []

    # --- Recipe Methods ---
    recipe_pname: str = ""
    recipe_mname: str = ""
    recipe_rquantity: str = ""
    editing_recipe_id: int = -1
    selected_pname_id: int = -1
    selected_mname_id: int = -1

    def set_product_selection(self, name: str):
        self.recipe_pname = name
        for p in self.products:
            if p[1] == name:
                self.selected_pname_id = p[0]
                break

    @rx.var
    def product_options(self) -> list[str]:
        return [p[1] for p in self.products]
    
    def set_material_selection(self, name: str):
        self.recipe_mname = name
        for p in self.materials:
            if p[1] == name:
                self.selected_mname_id = p[0]
                break

    @rx.var
    def material_options(self) -> list[str]:
        return [p[1] for p in self.materials]

    def load_recipe_to_edit(self, recipe: list):
        self.editing_recipe_id = int(recipe[0])
        self.recipe_pname = str(recipe[1])
        self.recipe_mname = str(recipe[2])
        self.recipe_rquantity = str(recipe[3])
        self.set_product_selection(recipe[1])
        self.set_material_selection(recipe[2])

    def clear_recipe_form(self):
        self.editing_recipe_id = -1
        self.recipe_pname = ""
        self.recipe_mname = ""
        self.recipe_rquantity = ""
        self.selected_pname_id: int = -1
        self.selected_mname_id: int = -1

    def handle_recipe_submit(self, form_data: dict):
        self.recipe_rquantity = form_data.get("recipe_quantity", "")
        form_material_name = form_data.get("material_name")
        form_product_name = form_data.get("product_name")

        if form_material_name: self.set_material_selection(form_material_name)
        if form_product_name: self.set_product_selection(form_product_name)
        return self.save_recipe()

    def save_recipe(self):
        try:
            quantity_val = float(self.recipe_rquantity) if self.recipe_rquantity else 0
        except ValueError:
            return rx.toast.error("Quantity must be a number.")
        
        try:
            if self.editing_recipe_id == -1:
                success, msg = self.run_db_query(db.insert_recipe, self.selected_pname_id, self.selected_mname_id, quantity_val)
            else:
                success, msg = self.run_db_query(db.update_recipe, self.editing_recipe_id, self.selected_pname_id, self.selected_mname_id, quantity_val)
            
            if success:
                self.get_all_recipes()
                self.clear_recipe_form()
                return rx.toast.success(msg)
            return rx.toast.error(msg)
        except Exception as e:
            return rx.toast.error(f"Recipe save failed: {str(e)}")

    def delete_recipe(self, recipe_id: int):
        try:
            success, msg = self.run_db_query(db.delete_recipe, recipe_id)
            if success:
                self.get_all_recipes()
                return rx.toast.success(msg)
            return rx.toast.error(msg)
        except Exception as e:
            return rx.toast.error(f"Delete failed: {str(e)}")
    
    filter_product_name: str = "All Products"
    @rx.var
    def filter_product_options(self) -> list[str]:
        return ["All Products", *self.product_options] 
      
    def set_filter_and_load(self, name: str):
        self.filter_product_name = name
        if name == "All Products":
            return self.get_all_recipes()
        
        selected_filter_id = -1
        for p in self.products:
            if p[1] == name:
                selected_filter_id = p[0]
                break
        
        if selected_filter_id != -1:
            self.get_selected_recipes(selected_filter_id)

    def get_selected_recipes(self, selected_filter_id):
        try:
            raw_recipe = self.run_db_query(db.get_selected_recipes, selected_filter_id)
            self.recipes = [list(recipe) for recipe in raw_recipe] if raw_recipe else []
        except Exception:
            self.recipes = []

    @rx.var
    def total_recipe_cost(self) -> float:
        total = 0
        for item in self.recipes:
            total += float(item[3]) * float(item[4])
        return total
    
    def get_all_recipes(self):
        try:
            raw_recipes = self.run_db_query(db.get_all_recipes)
            self.recipes = [list(recipe) for recipe in raw_recipes] if raw_recipes else []
        except Exception:
            self.recipes = []

    # --- Reports & History ---
    def get_reports(self):
        try:
            raw_reports = self.run_db_query(db.get_reports)     
            self.reports = [list(report) for report in raw_reports] if raw_reports else []
        except Exception:
            self.reports = []

    @rx.var
    def chart_data(self) -> list[dict]:
        return [
            {"Product": report[0], "Selling Price (RM)": report[1]/100, "Profit (RM)": report[4]/100} 
            for report in self.reports
        ]
    
    def get_material_history(self):
        try:
            raw_history = self.run_db_query(db.get_material_history)
            self.material_history = [list(hist) for hist in raw_history] if raw_history else []
        except Exception:
            self.material_history = []

    @rx.var
    def chart_material_history(self) -> list[dict]:
        wide_data = {}
        for history in self.material_history:
            material_name = history[0]
            price = history[1] / 100
            date_val = history[2]
            date_str = date_val.strftime("%Y-%m-%d") if hasattr(date_val, "strftime") else str(date_val)[:10]
            
            if date_str not in wide_data: wide_data[date_str] = {"date": date_str}
            wide_data[date_str][material_name] = price
                
        return sorted(wide_data.values(), key=lambda x: x["date"])

    @rx.var
    def material_names(self) -> list[str]:
        return list(set(hist[0] for hist in self.material_history))

# --- Routing ---
from .pages.materials import materials_page
from .pages.products import products_page
from .pages.recipes import recipes_page
from .pages.reports import reports_page
from .pages.history import history_page

app = rx.App()
app.add_page(materials_page, route="/")
app.add_page(products_page, route="/products")
app.add_page(recipes_page, route="/recipes")
app.add_page(reports_page, route="/reports")
app.add_page(history_page, route="/history")