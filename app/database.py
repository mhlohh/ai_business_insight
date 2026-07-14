import logging
import json
import os
import inspect
from typing import List, Dict, Any, Optional
from app.schemas.Database_schema import Product, Review, AnalysisCache
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.pool import NullPool

# ==========================================
# 1. DATABASE CONFIGURATION (NullPool Enabled)
# ==========================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DatabaseManager")

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

    async def wrapper(*args, **kwargs):
        func_name = func.__name__
        # Opens a brand new connection directly to the file every time
        session = SessionLocal()
        try:
            if inspect.iscoroutinefunction(func):
                result = await func(session, *args, **kwargs)
            else:
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
async def all_products(db) -> List[Dict[str, Any]]:
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
async def get_product(db, product_id: int) -> Optional[Dict[str, Any]]:
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
async def get_raw_reviews(db, product_id: int) -> List[str]:
    reviews = db.query(Review).filter(Review.product_id == product_id).all()
    return [r.body for r in reviews]


@db_safeguard
async def add_review(db, product_id: int, review_text: str):
    db.add(Review(product_id=product_id, body=review_text))
    # Invalidate the cache since the database has a new review
    db.query(AnalysisCache).filter(AnalysisCache.product_id == product_id).delete()
    db.commit()
    return {
        "status": "success",
        "message": "Review added and cache invalidated successfully.",
    }


@db_safeguard
async def check_insights(db, product_id: int) -> Optional[Dict[str, Any]]:
    cache = (
        db.query(AnalysisCache).filter(AnalysisCache.product_id == product_id).first()
    )
    if cache:
        return {"analysis": cache.analysis}
    return None


@db_safeguard
async def save_insights(db, product_id: int, insight_data):
    if isinstance(insight_data, dict):
        if "data" in insight_data:
            analysis_data = insight_data["data"]
        else:
            analysis_data = insight_data
        if hasattr(analysis_data, "model_dump"):
            analysis_data = analysis_data.model_dump()
        analysis_str = json.dumps(analysis_data)
    elif isinstance(insight_data, str):
        analysis_str = insight_data
    else:
        analysis_str = json.dumps(insight_data)

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
async def delete_insights(db, product_id: int):
    cache = (
        db.query(AnalysisCache).filter(AnalysisCache.product_id == product_id).first()
    )
    if not cache:
        return False
    db.query(AnalysisCache).filter(AnalysisCache.product_id == product_id).delete()
    db.commit()
    return True
