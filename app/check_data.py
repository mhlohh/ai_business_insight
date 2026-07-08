import sqlite3

conn = sqlite3.connect("litmus7.db")
cursor = conn.cursor()

cursor.execute("""
SELECT name, COUNT(reviews.id) AS review_count
FROM products
JOIN reviews
ON products.id = reviews.product_id
GROUP BY products.id
ORDER BY review_count DESC
LIMIT 10;
""")

for name, count in cursor.fetchall():
    print(f"{count} reviews - {name}")

conn.close()