import sqlite3

# Point this to your mock database
DB_NAME = "litmus7.db"

def all_products():
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM Products")
        rows = cur.fetchall()
        return [dict(row) for row in rows]

def check_insights(product_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT analysis FROM analysis_cache WHERE product_id = ?", (product_id,))
        row = cur.fetchone()
        if row:
            return dict(row)
        return None

def get_raw_reviews(product_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT review_text FROM Reviews WHERE product_id = ?", (product_id,))
        rows = cur.fetchall()
        return [row[0] for row in rows]

def save_insights(product_id: int, insight_text: str):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Insights (product_id, insight_text) VALUES (?, ?)", 
            (product_id, insight_text)
        )
        conn.commit()
print(all_products())
print(check_insights(1))