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
                
        # 3. Create engine with resilience settings for cloud environments
        self.engine = create_engine(
            self.db_url,
            pool_pre_ping=True,  # Checks connection health before every query
            pool_recycle=300,    # Refreshes connections every 5 minutes
            pool_size=5,
            max_overflow=10
        )
        
        # 4. Build/Sync tables on startup
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
                    unit TEXT,
                    supplier TEXT
                )
            '''))

            # Products Table
            conn.execute(text(f'''
                CREATE TABLE IF NOT EXISTS products (
                    id {pk_type},
                    name TEXT NOT NULL UNIQUE,
                    selling_price INTEGER NOT NULL,
                    labor_cost INTEGER DEFAULT 0,
                    overhead_cost INTEGER DEFAULT 0
                )
            '''))

            # Recipes (BOM) Table
            conn.execute(text(f'''
                CREATE TABLE IF NOT EXISTS recipes (
                    id {pk_type},
                    product_id INTEGER,
                    material_id INTEGER,
                    quantity REAL NOT NULL,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                    FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE
                )
            '''))

            # Price History Table
            conn.execute(text(f'''
                CREATE TABLE IF NOT EXISTS price_history (
                    id {pk_type},
                    material_id INTEGER,
                    old_price INTEGER,
                    new_price INTEGER,
                    change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE
                )
            '''))

            # Trigger logic for price tracking
            if is_postgres:
                # Postgres Trigger Function
                conn.execute(text('''
                    CREATE OR REPLACE FUNCTION log_price_changes()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        IF (OLD.unit_cost IS DISTINCT FROM NEW.unit_cost) THEN
                            INSERT INTO price_history(material_id, old_price, new_price)
                            VALUES(OLD.id, OLD.unit_cost, NEW.unit_cost);
                        END IF;
                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                '''))
                conn.execute(text('''
                    DROP TRIGGER IF EXISTS trg_price_update ON materials;
                    CREATE TRIGGER trg_price_update
                    AFTER UPDATE ON materials
                    FOR EACH ROW EXECUTE FUNCTION log_price_changes();
                '''))
            else:
                # SQLite Trigger
                conn.execute(text('''
                    CREATE TRIGGER IF NOT EXISTS trg_price_update
                    AFTER UPDATE OF unit_cost ON materials
                    BEGIN
                        INSERT INTO price_history(material_id, old_price, new_price)
                        VALUES(OLD.id, OLD.unit_cost, NEW.unit_cost);
                    END;
                '''))
            conn.commit()

    # --- Materials Logic ---
    def insert_material(self, name, cost, unit, supplier):
        try:
            with self.get_conn() as conn:
                conn.execute(text('''
                    INSERT INTO materials (name, unit_cost, unit, supplier) 
                    VALUES (:name, :cost, :unit, :supplier)
                '''), {"name": name, "cost": cost, "unit": unit, "supplier": supplier})
                conn.commit()
                return True, f"Added {name} successfully."
        except IntegrityError:
            return False, "Material name already exists."

    def update_material(self, mat_id, name, cost, unit, supplier):
        with self.get_conn() as conn:
            conn.execute(text('''
                UPDATE materials 
                SET name = :name, unit_cost = :cost, unit = :unit, supplier = :supplier
                WHERE id = :id
            '''), {"name": name, "cost": cost, "unit": unit, "supplier": supplier, "id": mat_id})
            conn.commit()
            return True, "Material updated."

    def get_materials(self):
        with self.get_conn() as conn:
            return conn.execute(text("SELECT id, name, unit_cost, unit, supplier FROM materials ORDER BY name ASC")).fetchall()

    def delete_material(self, mat_id):
        with self.get_conn() as conn:
            conn.execute(text("DELETE FROM materials WHERE id = :id"), {"id": mat_id})
            conn.commit()
            return True, "Material deleted."

    # --- Products Logic ---
    def insert_product(self, name, sell, labor, overhead):
        try:
            with self.get_conn() as conn:
                conn.execute(text('''
                    INSERT INTO products (name, selling_price, labor_cost, overhead_cost) 
                    VALUES (:name, :sell, :labor, :overhead)
                '''), {"name": name, "sell": sell, "labor": labor, "overhead": overhead})
                conn.commit()
                return True, f"Created {name} product."
        except IntegrityError:
            return False, "Product name already exists."

    def update_product(self, prod_id, name, sell, labor, overhead):
        with self.get_conn() as conn:
            conn.execute(text('''
                UPDATE products 
                SET name = :name, selling_price = :sell, labor_cost = :labor, overhead_cost = :overhead
                WHERE id = :id
            '''), {"name": name, "sell": sell, "labor": labor, "overhead": overhead, "id": prod_id})
            conn.commit()
            return True, "Product updated."

    def get_products(self):
        with self.get_conn() as conn:
            return conn.execute(text("SELECT id, name, selling_price, labor_cost, overhead_cost FROM products ORDER BY name ASC")).fetchall()

    def delete_product(self, prod_id):
        with self.get_conn() as conn:
            conn.execute(text("DELETE FROM products WHERE id = :id"), {"id": prod_id})
            conn.commit()
            return True, "Product deleted."

    # --- Recipes Logic ---
    def insert_recipe(self, product_id, material_id, quantity):
        with self.get_conn() as conn:
            conn.execute(text('''
                INSERT INTO recipes (product_id, material_id, quantity) 
                VALUES (:p_id, :m_id, :qty)
            '''), {"p_id": product_id, "m_id": material_id, "qty": quantity})
            conn.commit()
            return True, "Added to recipe."

    def update_recipe(self, recipe_id, product_id, material_id, quantity):
        with self.get_conn() as conn:
            conn.execute(text('''
                UPDATE recipes 
                SET product_id = :p_id, material_id = :m_id, quantity = :qty
                WHERE id = :id
            '''), {"p_id": product_id, "m_id": material_id, "qty": quantity, "id": recipe_id})
            conn.commit()
            return True, "Recipe updated."

    def get_all_recipes(self):
        with self.get_conn() as conn:
            query = text('''
                SELECT r.id, p.name, m.name, r.quantity, m.unit_cost, m.unit, m.supplier
                FROM recipes r
                JOIN products p ON r.product_id = p.id
                JOIN materials m ON r.material_id = m.id
                ORDER BY p.name ASC
            ''')
            return conn.execute(query).fetchall()

    def get_selected_recipes(self, product_id):
        with self.get_conn() as conn:
            query = text('''
                SELECT r.id, p.name, m.name, r.quantity, m.unit_cost, m.unit, m.supplier
                FROM recipes r
                JOIN products p ON r.product_id = p.id
                JOIN materials m ON r.material_id = m.id
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
                ORDER BY ph.change_date ASC
            ''')
            return conn.execute(query).fetchall()