import os
import ssl
import urllib.request
import pandas as pd
import sqlite3
import json

# Disable SSL verification for urllib requests (needed on macOS in some environments)
ssl._create_default_https_context = ssl._create_unverified_context

# Database Connection Settings
DB_FILE = "data/litmus7.db"

# Pre-defined Products
DEFAULT_PRODUCTS = [
    {
        "id": 1,
        "asin": "B018Y229OU",
        "name": "Fire Tablet, 7 Display, Wi-Fi, 8 GB",
        "description": "Amazon Fire Tablet with 7-inch display, Wi-Fi, 8 GB storage.",
        "price": 49.99,
        "quantity": 100,
    },
    {
        "id": 2,
        "asin": "B00L9EPT8O",
        "name": "Amazon Echo (White)",
        "description": "Amazon Echo smart speaker with Alexa.",
        "price": 89.99,
        "quantity": 50,
    },
]


def get_connection():
    """Returns a new SQLite3 connection with row factory configured to Row."""
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    """
    Creates SQLite3 tables and populates them with initial products and Amazon reviews.
    Uses the 1429_1.csv Kaggle dataset if available.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Create Schema
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            asin TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            price REAL,
            quantity INTEGER
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            body TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS analysis_cache (
            product_id INTEGER PRIMARY KEY,
            analysis TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """
    )
    conn.commit()

    # Check if database is already populated
    cursor.execute("SELECT COUNT(*) FROM reviews")
    if cursor.fetchone()[0] > 0:
        print("💾 Database already populated in SQLite. Skipping initialization.")
        conn.close()
        return

    print("🚀 Initializing database with products and reviews from 1429_1.csv...")

    csv_path = "1429_1.csv"
    if not os.path.exists(csv_path):
        print(
            f"⚠️ {csv_path} not found. Ensure the dataset is downloaded to use auto-initialization."
        )
        conn.close()
        return

    try:
        print(f"Reading {csv_path}...")
        df = pd.read_csv(csv_path, low_memory=False)

        # Drop rows without ASIN or review text
        df = df.dropna(subset=["asins", "reviews.text", "name"])

        # Get first ASIN for each row
        df["primary_asin"] = df["asins"].apply(lambda x: str(x).split(",")[0].strip())

        unique_products = df.drop_duplicates(subset=["primary_asin"])

        # Insert products
        for _, row in unique_products.iterrows():
            cursor.execute(
                "INSERT OR IGNORE INTO products (asin, name, description, price, quantity) VALUES (?, ?, ?, ?, ?)",
                (
                    row["primary_asin"],
                    row["name"],
                    str(row.get("categories", "")),
                    0.0,
                    0,
                ),
            )
        conn.commit()

        # Now fetch product IDs
        cursor.execute("SELECT asin, id FROM products")
        asin_to_id = {r["asin"]: r["id"] for r in cursor.fetchall()}

        # Insert reviews
        reviews_to_insert = []
        for _, row in df.iterrows():
            asin = row["primary_asin"]
            product_id = asin_to_id.get(asin)
            body = row["reviews.text"]

            if product_id and pd.notna(body):
                reviews_to_insert.append((product_id, str(body)))

        cursor.executemany(
            "INSERT INTO reviews (product_id, body) VALUES (?, ?)", reviews_to_insert
        )
        conn.commit()
        print("🎉 Database Initialization Completed Successfully!")
    except Exception as e:
        print(f"❌ Error populating dataset: {e}")
    finally:
        conn.close()


# Run initialization upon import
initialize_database()

# Database helper functions


def get_products() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, asin, name, description, price, quantity FROM products")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_product(product_id: int) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, asin, name, description, price, quantity FROM products WHERE id = ?",
        (product_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_reviews(product_id: int) -> list[str]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT body FROM reviews WHERE product_id = ?", (product_id,))
    rows = cursor.fetchall()
    conn.close()
    return [r["body"] for r in rows]


def add_review(product_id: int, review_text: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reviews (product_id, body) VALUES (?, ?)",
        (product_id, review_text),
    )
    conn.commit()
    conn.close()
    # Invalidate the cache since database has a new review
    clear_cache(product_id)


def get_cached_analysis(product_id: int) -> list[dict] | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT analysis FROM analysis_cache WHERE product_id = ?", (product_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row["analysis"])
        except Exception:
            return None
    return None


def cache_analysis(product_id: int, analysis: list[dict]):
    conn = get_connection()
    cursor = conn.cursor()
    analysis_str = json.dumps(analysis)
    cursor.execute(
        "INSERT OR REPLACE INTO analysis_cache (product_id, analysis) VALUES (?, ?)",
        (product_id, analysis_str),
    )
    conn.commit()
    conn.close()


def clear_cache(product_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM analysis_cache WHERE product_id = ?", (product_id,))
    conn.commit()
    conn.close()
