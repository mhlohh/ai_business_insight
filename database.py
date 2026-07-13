import logging
import json
import os
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.pool import NullPool  # Used to totally disable pooling

# Import your pre-defined project models directly
from app.schemas.models import Base, Product, Review, AnalysisCache

# ==========================================
# 1. PYDANTIC APPLICATION SCHEMA (Validation)
# ==========================================
VALID_CATEGORIES = {"quality", "support", "price", "usability", "other"}

CATEGORY_WEIGHTS = {
    "quality": 1.5,
    "support": 1.2,
    "price": 1.0,
    "usability": 1.3,
    "other": 1.0
}


# ==========================================
# 2. DATABASE CONFIGURATION (NullPool Enabled)
# ==========================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DatabaseManager")

DB_FILE = "data/litmus7.db"
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_FILE}"

# poolclass=NullPool guarantees no background connections are retained.
# connect_args resolves multi-threading limits for simple local operations.
engine = create_engine(
    DATABASE_URL, 
    poolclass=NullPool,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
                return {"status": "error", "message": f"Table missing error in [{func_name}]: {str(e)}"}
            elif "locked" in error_msg or "busy" in error_msg:
                return {"status": "error", "message": f"Database locked/busy under high load in [{func_name}]: {str(e)}"}
            return {"status": "error", "message": f"Operational database error in [{func_name}]: {str(e)}"}
        except SQLAlchemyError as e:
            session.rollback()
            return {"status": "error", "message": f"Database execution error in [{func_name}]: {str(e)}"}
        except Exception as e:
            session.rollback()
            return {"status": "error", "message": f"Unexpected system failure in [{func_name}]: {str(e)}"}
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
        print(" Database schemas initialized successfully.")
    except Exception as e:
        print(f" Initialization failure: {e}")


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
    reviews = db.query(Review.body).filter(Review.product_id == product_id).all()
    return [r.body for r in reviews]


@db_safeguard
def add_review(db, product_id: int, review_text: str):
    db.add(Review(product_id=product_id, body=review_text))
    # Clear cache directly in the same transaction
    db.query(AnalysisCache).filter(AnalysisCache.product_id == product_id).delete()
    db.commit()
    return {"status": "success", "message": "Review added and cache invalidated successfully."}


@db_safeguard
def get_cached_analysis(db, product_id: int) -> Optional[Dict[str, Any]]:
    cache = db.query(AnalysisCache).filter(AnalysisCache.product_id == product_id).first()
    if cache:
        try:
            raw_data = json.loads(cache.analysis)
            # Validates data through Pydantic to ensure schema integrity
            validated_data = InsightsList(**raw_data)
            return validated_data.model_dump()
        except Exception:
            return None
    return None


@db_safeguard
def cache_analysis(db, product_id: int, insights_data: InsightsList):
    """Serializes a validated Pydantic InsightsList object to JSON and caches it."""
    analysis_str = json.dumps(insights_data.model_dump())
    
    cache = db.query(AnalysisCache).filter(AnalysisCache.product_id == product_id).first()
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
    return {"status": "success", "message": "All AI insights have been permanently deleted from cache."}