import sqlite3
import os

class DatabaseManager:
    def __init__(self, db_name='bom_audit.db'):
        # We call the setup process when the class is initialized
        self.db_name = db_name
        # Only run setup if the file doesn't exist yet
        if not os.path.exists(self.db_name):
            self.create_database()
            print(f"Database '{self.db_name}' initialized for the first time.")

    def get_conn(self):
        conn = sqlite3.connect(self.db_name)
        conn.execute("PRAGMA foreign_keys = ON") # Turn on FK enforcement
        return conn

    def create_database(self):
        # Use connection helper
        with self.get_conn() as conn:
            cursor = conn.cursor()

            print("Creating tables...")

            # Create Tables (Materials, Products, Recipes, Price_History)
            cursor.execute('''CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                unit_cost INTEGER NOT NULL,
                unit TEXT NOT NULL,
                supplier TEXT)''')

            # Product name unique to prevent confusion if enter same name
            cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                selling_price INTEGER NOT NULL,
                labor_cost INTEGER NOT NULL,
                overhead_cost INTEGER DEFAULT 0)''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                material_id INTEGER,
                quantity FLOAT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products (id),
                FOREIGN KEY (material_id) REFERENCES materials (id))''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                material_id INTEGER,
                old_price INTEGER,
                new_price INTEGER,
                change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (material_id) REFERENCES materials (id) ON DELETE CASCADE)''')

    def insert_material(self, name, unit_cost, unit, supplier):
            """Insert materials and log initial price"""
            
            if unit_cost < 0:
                return False, "Unit cost cannot be negative."

            try:
                with self.get_conn() as conn:
                    cursor = conn.cursor()

                    # 1. Insert the material
                    query = 'INSERT INTO materials (name, unit_cost, unit, supplier) VALUES (?, ?, ?, ?)'
                    cursor.execute(query, (name, unit_cost, unit, supplier))
                    
                    # Get the auto-generated ID
                    new_id = cursor.lastrowid

                    # 2. Log the initial price (Old price set to 0 to show it's new)
                    cursor.execute('''
                        INSERT INTO price_history (material_id, old_price, new_price, change_date)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (new_id, 0, unit_cost))

                    # Instead of just True, returning the ID is very helpful!
                    return True, f"Material {name} inserted with ID: {new_id}"

            except sqlite3.IntegrityError:
                return False, f"A material with the name '{name}' already exists."
            except sqlite3.Error as e:
                raise Exception(f"Database error: {e}")

    def update_material(self, material_id, name, unit_cost, unit, supplier):
        """Update material details and log price changes if the cost has changed."""

        if unit_cost < 0:
            return False, "Price cannot be negative."

        try:
            with self.get_conn() as conn:
                cursor = conn.cursor()

                # 1. Fetch existing data to compare price and ensure material exists
                cursor.execute('SELECT name, unit_cost, unit, supplier FROM materials WHERE id = ?', (material_id,))
                result = cursor.fetchone()
                
                if not result:
                    return False, f"Material with ID {material_id} not found."
                
                old_name, old_price, old_unit, old_supplier = result

                # 2. Update the material details
                cursor.execute('''
                    UPDATE materials 
                    SET name = ?, unit_cost = ?, unit = ?, supplier = ? 
                    WHERE id = ?
                ''', (name, unit_cost, unit, supplier, material_id))

                # 3. Log to price_history ONLY if the price actually changed
                if old_price != unit_cost:
                    cursor.execute('''
                        INSERT INTO price_history (material_id, old_price, new_price, change_date)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (material_id, old_price, unit_cost))
                    
                    message = f"Material updated. Price changed from RM{old_price/100:.2f} to RM{unit_cost/100:.2f}."
                else:
                    message = "Material details updated successfully."

                return True, message

        except sqlite3.Error as e:
            raise Exception(f"Database error: {e}")
 
    def delete_material(self, material_id):
        try:
            # Use connection helper
            with self.get_conn() as conn:
                cursor = conn.cursor()
                
                # 1. Check if the material is being used in any recipes first
                cursor.execute('SELECT COUNT(*) FROM recipes WHERE material_id = ?', (material_id,))
                count = cursor.fetchone()[0]
                
                if count > 0:
                    # Return False and a clear error message
                    return False, f"Cannot delete. This material is used in {count} product recipes."

                # 2. If not used, delete it. 
                # (Because of ON DELETE CASCADE, price_history is deleted automatically!)
                cursor.execute('DELETE FROM materials WHERE id = ?', (material_id,))
                # 3. Check if the item actually existed to be deleted
                if cursor.rowcount == 0:
                    return False, "Material not found."

                # Success!
                return True, f"Material ID {material_id} has been deleted."

        except sqlite3.Error as e:
            # Raise exception to be caught by the API's 500 handler
            raise Exception(f"Database error: {e}")           

    def get_materials(self):
        """Retrieve all materials"""
        try:
            # Use connection helper
            with self.get_conn() as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM materials')
                materials = cursor.fetchall()
                if not materials:
                        return False
                return materials

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []

    def insert_product(self, name, selling_price, labor_cost, overhead_cost):
        """Insert products"""

        if min(selling_price, labor_cost, overhead_cost) < 0:
            return False, "Cost cannot be negative."

        try:
            # Use connection helper
            with self.get_conn() as conn:
                cursor = conn.cursor()

                query = 'INSERT INTO products (name, selling_price, labor_cost, overhead_cost) VALUES (?, ?, ?, ?)'
                cursor.execute(query, (name, selling_price, labor_cost, overhead_cost))

                # Get the auto-generated ID
                new_id = cursor.lastrowid
                return True, f"Product {name} inserted with ID: {new_id}"

        except sqlite3.IntegrityError:
                return False, f"A product with the name '{name}' already exists."
        except sqlite3.Error as e:
            # Raise exception to be caught by the API's 500 handler
            raise Exception(f"Database error: {e}")

    def update_product(self, product_id, name, selling_price, labor_cost, overhead_cost):
        """Update product pricing details"""

        if min(selling_price, labor_cost, overhead_cost) < 0:
            return False, "Cost cannot be negative."

        try:
            # Use connection helper
            with self.get_conn() as conn:
                cursor = conn.cursor()

                # Update the product pricing details
                cursor.execute('''UPDATE products 
                                SET name = ?, selling_price = ?, labor_cost = ?, overhead_cost = ? 
                                WHERE id = ?''', (name, selling_price, labor_cost, overhead_cost, product_id))
                if cursor.rowcount == 0:
                    return False, f"Product with ID {product_id} not found."

                # Success!
                return True, f"Product ID {product_id} pricing updated."

        except sqlite3.Error as e:
            # Raise exception to be caught by the API's 500 handler
            raise Exception(f"Database error: {e}")

    def delete_product(self, product_id):
        """Delete product by ID"""

        try:
            # Use connection helper
            with self.get_conn() as conn:
                cursor = conn.cursor()

                # Delete the product
                cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))

                # If no rows were affected, the ID didn't exist
                if cursor.rowcount == 0:
                    return False, f"Product ID {product_id} not found."
                return True, f"Product ID {product_id} has been deleted."

        except sqlite3.Error as e:
            # Raise exception to be caught by the API's 500 handler
            raise Exception(f"Database error: {e}")

    def get_products(self):
        """Retrieve all products"""
        try:
            # Use connection helper
            with self.get_conn() as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM products')
                products = cursor.fetchall()
                if not products:
                        return False
                return products

        except sqlite3.Error as e:
            # Raise exception to be caught by the API's 500 handler
            raise Exception(f"Database error: {e}")

    def insert_recipe(self, product_id, material_id, quantity):
        """Insert recipe"""
        if quantity < 0:
            return False, "Quantity cannot be negative."

        try:
            # Use connection helper
            with self.get_conn() as conn:
                cursor = conn.cursor()

                query = 'INSERT INTO recipes (product_id, material_id, quantity) VALUES (?, ?, ?)'
                cursor.execute(query, (product_id, material_id, quantity))
                
                if cursor.rowcount == 0:
                    return False, "Failed to insert Recipe."

                # Success!
                return True, f"Recipe for product ID {product_id} has been assigned."

        except sqlite3.Error as e:
            # Raise exception to be caught by the API's 500 handler
            raise Exception(f"Database error: {e}")

    def update_recipe(self, recipe_id, product_id, material_id, quantity):
        """Update recipe quantity"""
        
        # Validation logic
        if quantity < 0:
            return False, "Quantity cannot be negative."
        try:
            with self.get_conn() as conn:
                cursor = conn.cursor()

                # Update the recipe quantity
                cursor.execute(
                    'UPDATE recipes SET product_id = ?, material_id = ?, quantity = ? WHERE id = ?', 
                    (product_id, material_id, quantity, recipe_id)
                )
                
                # Check if the row actually existed
                if cursor.rowcount == 0:
                    return False, f"Recipe ID {recipe_id} not found."

                # Success
                return True, f"Recipe ID {recipe_id} updated."

        except sqlite3.Error as e:
            # Pass the database error up to the API's 500 handler
            raise Exception(f"Database error: {e}")

    def delete_recipe(self, recipe_id):
        """Delete recipe by ID"""
        try:
            # Use connection helper
            with self.get_conn() as conn:
                cursor = conn.cursor()

                # Delete the recipe
                cursor.execute('DELETE FROM recipes WHERE id = ?', (recipe_id,))
                # If no rows were affected, the ID didn't exist
                if cursor.rowcount == 0:
                    return False, f"Recipe ID {recipe_id} not found."
                return True, f"Recipe ID {recipe_id} has been deleted."

        except sqlite3.Error as e:
            # Raise exception to be caught by the API's 500 handler
            raise Exception(f"Database error: {e}")

    def get_selected_recipes(self, product_id):
        """Retrieve recipe for a specific product"""
        try:
            # Use connection helper
            with self.get_conn() as conn:
                cursor = conn.cursor()

                cursor.execute('''SELECT 
                                r.id,
                                p.name,
                                m.name, 
                                r.quantity, 
                                m.unit_cost, 
                                m.unit, 
                                m.supplier
                            FROM recipes r
                            JOIN materials m ON r.material_id = m.id
                            JOIN products p ON r.product_id = p.id
                            WHERE r.product_id = ?''', (product_id,))
                recipes = cursor.fetchall()
                if not recipes:
                        return False
                return recipes

        except sqlite3.Error as e:
            # Raise exception to be caught by the API's 500 handler
            raise Exception(f"Database error: {e}")
        
    def get_all_recipes(self):
        """Retrieve all recipes for all products"""
        try:
            # Use connection helper
            with self.get_conn() as conn:
                cursor = conn.cursor()

                cursor.execute('''SELECT 
                                r.id,
                                p.name,
                                m.name, 
                                r.quantity, 
                                m.unit_cost, 
                                m.unit, 
                                m.supplier
                            FROM recipes r
                            JOIN materials m ON r.material_id = m.id
                            JOIN products p ON r.product_id = p.id''')
                
                recipes = cursor.fetchall()
                
                if not recipes:
                        return False
                return recipes

        except sqlite3.Error as e:
            # Raise exception to be caught by the API's 500 handler
            raise Exception(f"Database error: {e}")

    def calculate_product_cost(self, product_id):
        try:
            with self.get_conn() as conn:
                cursor = conn.cursor()

                # 1. Material Costs
                cursor.execute('''SELECT r.quantity, m.unit_cost 
                                FROM recipes r
                                JOIN materials m ON r.material_id = m.id
                                WHERE r.product_id = ?''', (product_id,))
                recipes = cursor.fetchall()
                
                if not recipes:
                    return None # Consistently return None if no data exists

                material_total = 0.0
                for quantity, unit_cost in recipes:
                    material_total += quantity * unit_cost

                # 2. Labor and Overhead
                cursor.execute('SELECT labor_cost, overhead_cost FROM products WHERE id = ?', (product_id,))
                product_info = cursor.fetchone()
                
                # Use a helper to handle missing product_info or NULL values
                if product_info:
                    labor = product_info[0] or 0
                    overhead = product_info[1] or 0
                else:
                    return None 

                # 3. Sum everything
                return [material_total, labor + overhead]

        except Exception:
            return None # If anything goes wrong, skip this item in the report

    def get_reports(self):
        try:
            with self.get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id, name, selling_price FROM products')
                products = cursor.fetchall()
                
                if not products:
                    return [] # Returning an empty list is better than False for loops
                    
                report = []
                for product_id, name, selling_price in products:
                    material_cost, other_cost = self.calculate_product_cost(product_id)
                    total_cost = material_cost + other_cost
                    if total_cost is None:
                        continue
                    
                    profit = selling_price - total_cost
                    margin = (profit / selling_price * 100) if selling_price != 0 else 0
                    
                    # Appending as a list [ ] is fine!
                    report.append([name, selling_price, total_cost, material_cost, profit, margin])
                    
                return report
        except Exception as e:
            raise Exception(f"Report generation error: {e}")
        
    def get_material_history(self):
        """Retrieve all history where price value is changed"""
        try:
            # Use connection helper
            with self.get_conn() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                SELECT m.name, ph.new_price, ph.change_date
                FROM price_history ph
                JOIN materials m ON ph.material_id = m.id
                WHERE material_id IN (
                    SELECT material_id
                    FROM price_history
                    GROUP BY material_id
                    HAVING COUNT(material_id) > 1
                )
                ''')
                history = cursor.fetchall()
                if not history:
                        return False
                return history

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []