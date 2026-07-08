import sqlite3

# Connect to SQLite database
conn = sqlite3.connect("litmus7.db")
cursor = conn.cursor()

# -------------------------------
# Products Table
# -------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    asin TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    price REAL,
    quantity INTEGER
)
""")

# -------------------------------
# Reviews Table
# -------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL,
    rating REAL,
    body TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id)
)
""")

# -------------------------------
# Analysis Cache Table
# -------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS analysis_cache (
    product_id INTEGER PRIMARY KEY,
    analysis TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id)
)
""")

# Save changes
conn.commit()

# Close connection
conn.close()

print("✅ Database and tables created successfully!")