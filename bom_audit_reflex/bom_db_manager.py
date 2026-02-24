import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

class DatabaseManager:
    def __init__(self):
        # 1. Get URL from environment or fallback to local SQLite
        self.db_url = os.getenv("DATABASE_URL", "sqlite:///bom_audit.db")
        
        # 2. Fix Neon SSL requirements (Neon requires sslmode=require)
        if self.db_url.startswith("postgresql") and "sslmode" not in self.db_url:
            separator = "&" if "?" in self.db_url else "?"
            self.db_url += f"{separator}sslmode=require"
                
        self.engine = create_engine(self.db_url)
        
        # 3. Build/Sync tables on startup
        self.create_database()

    def get_conn(self):
        """Returns a connection context manager."""
        return self.engine.connect()

    def create_database(self):
        """Creates tables compatible with both SQLite and Postgres."""
        is_postgres = self.db_url.startswith("postgresql")
        pk_type = "SERIAL PRIMARY KEY" if is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"

        with self.get_conn() as conn:
            # Materials Table
            conn.execute(text(f'''
                CREATE TABLE IF NOT EXISTS materials (
                    id {pk_type},
                    name TEXT NOT NULL UNIQUE,
                    unit_cost INTEGER NOT NULL,
                    unit TEXT NOT NULL,
                    supplier TEXT)
            '''))
            
            # Products Table
            conn.execute(text(f'''
                CREATE TABLE IF NOT EXISTS products (
                    id {pk_type},
                    name TEXT NOT NULL UNIQUE,
                    selling_price INTEGER NOT NULL,
                    labor_cost INTEGER NOT NULL,
                    overhead_cost INTEGER DEFAULT 0)
            '''))

            # Recipes Table
            conn.execute(text(f'''
                CREATE TABLE IF NOT EXISTS recipes (
                    id {pk_type},
                    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
                    material_id INTEGER REFERENCES materials(id) ON DELETE CASCADE,
                    quantity FLOAT NOT NULL)
            '''))

            # Price History Table
            conn.execute(text(f'''
                CREATE TABLE IF NOT EXISTS price_history (
                    id {pk_type},
                    material_id INTEGER REFERENCES materials(id) ON DELETE CASCADE,
                    old_price INTEGER,
                    new_price INTEGER,
                    change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
            '''))
            conn.commit()

    # --- Materials Logic ---
    def insert_material(self, name, unit_cost, unit, supplier):
        if unit_cost < 0: return False, "Unit cost cannot be negative."
        try:
            with self.get_conn() as conn:
                # Use RETURNING id for Postgres compatibility
                query = text('''
                    INSERT INTO materials (name, unit_cost, unit, supplier) 
                    VALUES (:name, :cost, :unit, :sup)
                    RETURNING id
                ''')
                result = conn.execute(query, {"name": name, "cost": unit_cost, "unit": unit, "sup": supplier})
                new_id = result.fetchone()[0]
                
                # Log Initial Price
                conn.execute(text('''
                    INSERT INTO price_history (material_id, old_price, new_price)
                    VALUES (:mid, 0, :new_p)
                '''), {"mid": new_id, "new_p": unit_cost})
                
                conn.commit()
                return True, f"Material {name} inserted with ID {new_id}."
        except IntegrityError:
            return False, f"Material '{name}' already exists."
        except Exception as e:
            print(f"DATABASE ERROR: {e}")
            return False, f"Error: {str(e)}"

    def update_material(self, material_id, name, unit_cost, unit, supplier):
        try:
            with self.get_conn() as conn:
                old = conn.execute(text("SELECT unit_cost FROM materials WHERE id = :id"), {"id": material_id}).fetchone()
                if not old: return False, "Material not found."
                
                conn.execute(text('''
                    UPDATE materials SET name = :n, unit_cost = :c, unit = :u, supplier = :s WHERE id = :id
                '''), {"n": name, "c": unit_cost, "u": unit, "s": supplier, "id": material_id})

                if old[0] != unit_cost:
                    conn.execute(text('''
                        INSERT INTO price_history (material_id, old_price, new_price)
                        VALUES (:id, :old, :new)
                    '''), {"id": material_id, "old": old[0], "new": unit_cost})
                
                conn.commit()
                return True, "Material updated."
        except Exception as e:
            return False, str(e)

    def delete_material(self, material_id):
        try:
            with self.get_conn() as conn:
                check = conn.execute(text("SELECT COUNT(*) FROM recipes WHERE material_id = :id"), {"id": material_id}).fetchone()
                if check[0] > 0:
                    return False, f"Used in {check[0]} recipes. Remove from recipes first."
                
                conn.execute(text("DELETE FROM materials WHERE id = :id"), {"id": material_id})
                conn.commit()
                return True, "Material deleted."
        except Exception as e:
            return False, str(e)

    def get_materials(self):
        with self.get_conn() as conn:
            return conn.execute(text("SELECT * FROM materials ORDER BY name ASC")).fetchall()

    # --- Products Logic ---
    def insert_product(self, name, selling_price, labor_cost, overhead_cost):
        try:
            with self.get_conn() as conn:
                query = text('''
                    INSERT INTO products (name, selling_price, labor_cost, overhead_cost) 
                    VALUES (:n, :s, :l, :o) RETURNING id
                ''')
                result = conn.execute(query, {"n": name, "s": selling_price, "l": labor_cost, "o": overhead_cost})
                conn.commit()
                return True, f"Product {name} created."
        except IntegrityError:
            return False, "Product name exists."

    def get_products(self):
        with self.get_conn() as conn:
            return conn.execute(text("SELECT * FROM products ORDER BY name ASC")).fetchall()

    def update_product(self, product_id, name, selling_price, labor_cost, overhead_cost):
        with self.get_conn() as conn:
            conn.execute(text('''
                UPDATE products SET name=:n, selling_price=:s, labor_cost=:l, overhead_cost=:o WHERE id=:id
            '''), {"n": name, "s": selling_price, "l": labor_cost, "o": overhead_cost, "id": product_id})
            conn.commit()
            return True, "Product updated."

    def delete_product(self, product_id):
        with self.get_conn() as conn:
            conn.execute(text("DELETE FROM products WHERE id = :id"), {"id": product_id})
            conn.commit()
            return True, "Product deleted."

    # --- Recipe Logic ---
    def insert_recipe(self, product_id, material_id, quantity):
        try:
            with self.get_conn() as conn:
                conn.execute(text('''
                    INSERT INTO recipes (product_id, material_id, quantity) 
                    VALUES (:pid, :mid, :q)
                '''), {"pid": product_id, "mid": material_id, "q": quantity})
                conn.commit()
                return True, "Recipe inserted."
        except Exception as e:
            return False, str(e)
        
    def update_recipe(self, recipe_id, product_id, material_id, quantity):
        with self.get_conn() as conn:
            conn.execute(text('''
                UPDATE recipes SET product_id=:p, material_id=:m, quantity=:q WHERE id=:id
            '''), {"p": product_id, "m": material_id, "q": quantity, "id": recipe_id})
            conn.commit()
            return True, "Recipe updated."

    def get_all_recipes(self):
        with self.get_conn() as conn:
            query = text('''
                SELECT r.id, p.name, m.name, r.quantity, m.unit_cost, m.unit, m.supplier
                FROM recipes r
                JOIN materials m ON r.material_id = m.id
                JOIN products p ON r.product_id = p.id
            ''')
            return conn.execute(query).fetchall()

    def get_selected_recipes(self, product_id):
        with self.get_conn() as conn:
            query = text('''
                SELECT r.id, p.name, m.name, r.quantity, m.unit_cost, m.unit, m.supplier
                FROM recipes r
                JOIN materials m ON r.material_id = m.id
                JOIN products p ON r.product_id = p.id
                WHERE r.product_id = :id
            ''')
            return conn.execute(query, {"id": product_id}).fetchall()

    def delete_recipe(self, recipe_id):
        with self.get_conn() as conn:
            conn.execute(text("DELETE FROM recipes WHERE id = :id"), {"id": recipe_id})
            conn.commit()
            return True, "Removed from recipe."

    # --- Reports Logic ---
    def get_reports(self):
        with self.get_conn() as conn:
            products = conn.execute(text("SELECT id, name, selling_price, labor_cost, overhead_cost FROM products")).fetchall()
            report = []
            for p_id, name, sell, labor, overhead in products:
                res = conn.execute(text('''
                    SELECT r.quantity, m.unit_cost FROM recipes r
                    JOIN materials m ON r.material_id = m.id WHERE r.product_id = :id
                '''), {"id": p_id}).fetchall()
                
                mat_cost = sum(q * c for q, c in res) if res else 0
                total_cost = mat_cost + labor + overhead
                profit = sell - total_cost
                margin = (profit / sell * 100) if sell != 0 else 0
                report.append([name, sell, total_cost, mat_cost, profit, margin])
            return report

    def get_material_history(self):
        with self.get_conn() as conn:
            query = text('''
                SELECT m.name, ph.new_price, ph.change_date
                FROM price_history ph
                JOIN materials m ON ph.material_id = m.id
                ORDER BY ph.change_date DESC
            ''')
            return conn.execute(query).fetchall()