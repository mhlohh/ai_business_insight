import logger
import json
import os
from typing import List, Dict, Any, Optional
from schemas.Database_schema import Product, Review, AnalysisCache
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.pool import NullPool

# ==========================================
# 1. DATABASE CONFIGURATION (NullPool Enabled)
# ==========================================
logger.basicConfig(level=logger.INFO)

DB_FILE = "data/litmus7.db"
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_FILE}"

# NullPool guarantees zero background connections are retained.
engine = create_engine(
    DATABASE_URL, poolclass=NullPool, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ==========================================
# 2. CENTRALIZED RELATIONAL SCHEMA
# ==========================================
Base = declarative_base()


# ==========================================
# 3. REUSABLE ERROR HANDLER DECORATOR
# ==========================================
def db_safeguard(func):
    """Decorator to catch database locks, missing tables, and system errors."""

    def wrapper(*args, **kwargs):
        func_name = func.__name__
        # Opens a brand new connection directly to the file every time
        session = SessionLocal()
        try:
            result = func(session, *args, **kwargs)
            return result
        except OperationalError as e:
            session.rollback()
            error_msg = str(e).lower()
            if "no such table" in error_msg:
                return {
                    "status": "error",
                    "message": f"Table missing error in [{func_name}]: {str(e)}",
                }
            elif "locked" in error_msg or "busy" in error_msg:
                return {
                    "status": "error",
                    "message": f"Database locked/busy under high load in [{func_name}]: {str(e)}",
                }
            return {
                "status": "error",
                "message": f"Operational database error in [{func_name}]: {str(e)}",
            }
        except SQLAlchemyError as e:
            session.rollback()
            return {
                "status": "error",
                "message": f"Database execution error in [{func_name}]: {str(e)}",
            }
        except Exception as e:
            session.rollback()
            return {
                "status": "error",
                "message": f"Unexpected system failure in [{func_name}]: {str(e)}",
            }
        finally:
            # Closes and drops the connection handle instantly
            session.close()

    return wrapper


# ==========================================
# 4. CORE DATABASE HELPER FUNCTIONS
# ==========================================


def initialize_database():
    """Creates SQLite3 tables using the imported metadata schema."""
    try:
        Base.metadata.create_all(bind=engine)
        print("💾 Database schemas initialized successfully.")
    except Exception as e:
        print(f"❌ Initialization failure: {e}")


@db_safeguard
def get_products(db) -> List[Dict[str, Any]]:
    products = db.query(Product).all()
    return [
        {
            "id": p.id,
            "asin": p.asin,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "quantity": p.quantity,
        }
        for p in products
    ]


@db_safeguard
def get_product(db, product_id: int) -> Optional[Dict[str, Any]]:
    p = db.query(Product).filter(Product.id == product_id).first()
    if p:
        return {
            "id": p.id,
            "asin": p.asin,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "quantity": p.quantity,
        }
    return None


@db_safeguard
def get_reviews(db, product_id: int) -> List[str]:
    reviews = db.query(Review).filter(Review.product_id == product_id).all()
    return [r.body for r in reviews]


@db_safeguard
def add_review(db, product_id: int, review_text: str):
    db.add(Review(product_id=product_id, body=review_text))
    # Invalidate the cache since the database has a new review
    db.query(AnalysisCache).filter(AnalysisCache.product_id == product_id).delete()
    db.commit()
    return {
        "status": "success",
        "message": "Review added and cache invalidated successfully.",
    }


@db_safeguard
def get_cached_analysis(db, product_id: int) -> Optional[List[Dict[str, Any]]]:
    cache = (
        db.query(AnalysisCache).filter(AnalysisCache.product_id == product_id).first()
    )
    if cache:
        try:
            # Convert the stored JSON string back into a Python list of dictionaries
            return json.loads(cache.analysis)
        except Exception:
            return None
    return None


@db_safeguard
def cache_analysis(db, product_id: int, analysis_data: List[Dict[str, Any]]):
    """Takes standard Python lists/dicts, converts to JSON, and saves to cache."""
    # Convert standard Python data to a JSON string for text column storage
    analysis_str = json.dumps(analysis_data)

    cache = (
        db.query(AnalysisCache).filter(AnalysisCache.product_id == product_id).first()
    )
    if cache:
        cache.analysis = analysis_str
    else:
        db.add(AnalysisCache(product_id=product_id, analysis=analysis_str))
    db.commit()
    return {"status": "success", "message": "Insights successfully cached."}


@db_safeguard
def clear_cache(db, product_id: int):
    db.query(AnalysisCache).filter(AnalysisCache.product_id == product_id).delete()
    db.commit()
    return {"status": "success", "message": "Cache permanently deleted."}
