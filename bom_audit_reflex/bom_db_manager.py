import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

class DatabaseManager:
    def __init__(self):
        # 1. Detect environment: Use Neon URL if available, else local SQLite
        self.db_url = os.getenv("DATABASE_URL", "sqlite:///bom_audit.db")
        
        # 2. Setup Engine (echo=False keeps your logs clean)
        self.engine = create_engine(self.db_url, echo=False)
        
        # 3. Always ensure tables exist on startup
        self.create_database()

    def get_conn(self):
        """Returns a connection context manager."""
        return self.engine.connect()

    def create_database(self):
        """Creates tables using syntax compatible with both SQLite and Postgres."""
        # Postgres uses SERIAL, SQLite uses AUTOINCREMENT
        is_postgres = self.db_url.startswith("postgresql")
        pk_type = "SERIAL PRIMARY KEY" if is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"

        with self.get_conn() as conn:
            # Materials
            conn.execute(text(f'''
                CREATE TABLE IF NOT EXISTS materials (
                    id {pk_type},
                    name TEXT NOT NULL UNIQUE,
                    unit_cost INTEGER NOT NULL,
                    unit TEXT NOT NULL,
                    supplier TEXT)
            '''))
            
            # Products
            conn.execute(text(f'''
                CREATE TABLE IF NOT EXISTS products (
                    id {pk_type},
                    name TEXT NOT NULL UNIQUE,
                    selling_price INTEGER NOT NULL,
                    labor_cost INTEGER NOT NULL,
                    overhead_cost INTEGER DEFAULT 0)
            '''))

            # Recipes
            conn.execute(text(f'''
                CREATE TABLE IF NOT EXISTS recipes (
                    id {pk_type},
                    product_id INTEGER REFERENCES products(id),
                    material_id INTEGER REFERENCES materials(id),
                    quantity FLOAT NOT NULL)
            '''))

            # Price History
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
                # 1. Insert Material (Standard SQL)
                query = text('''
                    INSERT INTO materials (name, unit_cost, unit, supplier) 
                    VALUES (:name, :cost, :unit, :sup)
                ''')
                result = conn.execute(query, {"name": name, "cost": unit_cost, "unit": unit, "sup": supplier})
                
                # 2. Get the ID (Works for both)
                new_id = result.lastrowid
                
                # 3. Log Initial Price
                conn.execute(text('''
                    INSERT INTO price_history (material_id, old_price, new_price)
                    VALUES (:mid, 0, :new_p)
                '''), {"mid": new_id, "new_p": unit_cost})
                
                conn.commit()
                return True, f"Material {name} inserted."
        except IntegrityError:
            return False, f"Material '{name}' already exists."

    def update_material(self, material_id, name, unit_cost, unit, supplier):
        try:
            with self.get_conn() as conn:
                # Fetch old price
                old = conn.execute(text("SELECT unit_cost FROM materials WHERE id = :id"), {"id": material_id}).fetchone()
                if not old: return False, "Material not found."
                
                # Update
                conn.execute(text('''
                    UPDATE materials SET name = :n, unit_cost = :c, unit = :u, supplier = :s WHERE id = :id
                '''), {"n": name, "c": unit_cost, "u": unit, "s": supplier, "id": material_id})

                # Log if price changed
                if old[0] != unit_cost:
                    conn.execute(text('''
                        INSERT INTO price_history (material_id, old_price, new_price)
                        VALUES (:id, :old, :new)
                    '''), {"id": material_id, "old": old[0], "new": unit_cost})
                
                conn.commit()
                return True, "Material updated."
        except Exception as e:
            return False, str(e)

    def get_materials(self):
        with self.get_conn() as conn:
            result = conn.execute(text("SELECT * FROM materials")).fetchall()
            return result if result else []

    # --- Products Logic ---
    def insert_product(self, name, selling_price, labor_cost, overhead_cost):
        try:
            with self.get_conn() as conn:
                query = text('''
                    INSERT INTO products (name, selling_price, labor_cost, overhead_cost) 
                    VALUES (:n, :s, :l, :o)
                ''')
                conn.execute(query, {"n": name, "s": selling_price, "l": labor_cost, "o": overhead_cost})
                conn.commit()
                return True, f"Product {name} created."
        except IntegrityError:
            return False, "Product name exists."

    def get_products(self):
        with self.get_conn() as conn:
            return conn.execute(text("SELECT * FROM products")).fetchall()

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
                return True, "Recipe added."
        except Exception as e:
            return False, str(e)

    def get_all_recipes(self):
        with self.get_conn() as conn:
            query = text('''
                SELECT r.id, p.name, m.name, r.quantity, m.unit_cost, m.unit, m.supplier
                FROM recipes r
                JOIN materials m ON r.material_id = m.id
                JOIN products p ON r.product_id = p.id
            ''')
            return conn.execute(query).fetchall()

    def delete_recipe(self, recipe_id):
        with self.get_conn() as conn:
            conn.execute(text("DELETE FROM recipes WHERE id = :id"), {"id": recipe_id})
            conn.commit()
            return True, "Recipe deleted."

    # --- Reports Logic ---
    def calculate_product_cost(self, product_id):
        with self.get_conn() as conn:
            # 1. Materials
            res = conn.execute(text('''
                SELECT r.quantity, m.unit_cost FROM recipes r
                JOIN materials m ON r.material_id = m.id WHERE r.product_id = :id
            '''), {"id": product_id}).fetchall()
            mat_total = sum(q * c for q, c in res) if res else 0
            
            # 2. Labor/Overhead
            prod = conn.execute(text("SELECT labor_cost, overhead_cost FROM products WHERE id = :id"), {"id": product_id}).fetchone()
            if not prod: return 0, 0
            return mat_total, (prod[0] + prod[1])

    def get_reports(self):
        report = []
        products = self.get_products()
        for p_id, name, sell, labor, overhead in products:
            mat_cost, other_cost = self.calculate_product_cost(p_id)
            total_cost = mat_cost + other_cost
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