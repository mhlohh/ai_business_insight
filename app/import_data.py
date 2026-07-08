import sqlite3
import pandas as pd

# Path to your CSV file
csv_path = r"C:\Users\csafe\Downloads\1429_1.csv"

# Read the CSV
df = pd.read_csv(csv_path, low_memory=False)

# Connect to the database
conn = sqlite3.connect("litmus7.db")
cursor = conn.cursor()

products_added = set()

for _, row in df.iterrows():

    product_id = str(row["id"])

    # Insert each product only once
    if product_id not in products_added:

        cursor.execute("""
        INSERT OR IGNORE INTO products
        (id, asin, name, description, price, quantity)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            product_id,
            str(row["asins"]) if pd.notna(row["asins"]) else "",
            str(row["name"]) if pd.notna(row["name"]) else "",
            None,
            None,
            None
        ))

        products_added.add(product_id)

    # Insert review
    review_text = row["reviews.text"]
    rating = row["reviews.rating"] if pd.notna(row["reviews.rating"]) else None

    if pd.notna(review_text):

        cursor.execute("""
        INSERT INTO reviews (product_id, rating, body)
        VALUES (?, ?, ?)
        """, (
            product_id,
            rating,
            str(review_text)
        ))

conn.commit()
conn.close()

print("✅ All products and reviews imported successfully!")