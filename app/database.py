import sqlite3
from app.logger import logger

# Point this to your mock database
DB_NAME = "app/litmus7.db"
def all_products():
    logger.info("DB - Fetching all products")
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(" SELECT id,name FROM products")
        rows = cur.fetchall()
        logger.info(f"DB - Fetched {len(rows)} products")
        return [dict(row) for row in rows]

def check_insights(product_id: int):
    logger.info(f"DB - Checking cached insights for product ID {product_id}")
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT analysis FROM analysis_cache WHERE product_id = ?", (product_id,))
        row = cur.fetchone()
        if row:
            logger.info(f"DB - Cache hit for product ID {product_id}")
            return dict(row)
        logger.info(f"DB - Cache miss for product ID {product_id}")
        return None

def get_raw_reviews(product_id: int):
    logger.info(f"DB - Fetching raw reviews for product ID {product_id}")
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT body FROM reviews WHERE product_id = ?", (product_id,))
        rows = cur.fetchall()
        logger.info(f"DB - Fetched {len(rows)} raw reviews for product ID {product_id}")
        return [row[0] for row in rows]
    

def save_insights(product_id: int, insight_text: str):
    logger.info(f"DB - Saving insights to cache for product ID {product_id}")
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO analysis_cache (product_id, analysis) VALUES (?, ?)", 
            (product_id, insight_text)
        )
        conn.commit()
    logger.info(f"DB - Successfully saved insights for product ID {product_id}")

def clear_insights(product_id: int):
    """One single function to handle the web request AND wipe the database."""
    logger.info(f"DB - Wiping analysis cache for product ID {product_id}")
    # 1. Open the database
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        
        # 2. Delete the data
        cur.execute("DELETE FROM analysis_cache WHERE product_id = ?", (product_id,))
        conn.commit()
    # 3. Send the success message back to the internet/browser
    logger.info(f"DB - Successfully wiped cache for product ID {product_id}")
    return {"status": "success", "message": "All AI insights have been permanently deleted."}
    
   

