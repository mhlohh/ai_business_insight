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
        cur.execute("SELECT body FROM reviews WHERE product_id = ?", (product_id,))
        rows = cur.fetchall()
        return [row[0] for row in rows]
    

def save_insights(product_id: int, insight_text: str):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO analysis_cache (product_id, analysis) VALUES (?, ?)", 
            (product_id, insight_text)
        )
        conn.commit()

def clear_all_insights(product_id: int):
    """One single function to handle the web request AND wipe the database."""
    
    # 1. Open the database
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        
        # 2. Delete the data
        cur.execute("DELETE FROM analysis_cache WHERE product_id = ?", (product_id,))
        conn.commit()
    # 3. Send the success message back to the internet/browser
    return {"status": "success", "message": "All AI insights have been permanently deleted."}
    
   

