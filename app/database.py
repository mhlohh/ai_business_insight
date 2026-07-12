import os
import ssl
import urllib.request
import pandas as pd
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.schemas.models import Base, Product, Review, AnalysisCache

# Disable SSL verification for urllib requests (needed on macOS in some environments)
ssl._create_default_https_context = ssl._create_unverified_context

# Database Connection Settings
DB_FILE = "data/litmus7.db"
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_FILE}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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


def initialize_database():
    """
    Creates SQLite3 tables and populates them with initial products and Amazon reviews.
    Uses the 1429_1.csv Kaggle dataset if available.
    """
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        if db.query(Review).count() > 0:
            print("💾 Database already populated in SQLite. Skipping initialization.")
            return

        print("🚀 Initializing database with products and reviews from 1429_1.csv...")

        csv_path = "data/1429_1.csv"
        if not os.path.exists(csv_path):
            print(
                f"⚠️ {csv_path} not found. Ensure the dataset is downloaded to use auto-initialization."
            )
            return

        try:
            print(f"Reading {csv_path}...")
            df = pd.read_csv(csv_path, low_memory=False)

            # Drop rows without ASIN or review text
            df = df.dropna(subset=["asins", "reviews.text", "name"])

            # Get first ASIN for each row
            df["primary_asin"] = df["asins"].apply(
                lambda x: str(x).split(",")[0].strip()
            )

            # Clean product names: take only the first line to remove CSV noise
            df["clean_name"] = df["name"].apply(
                lambda x: str(x).split("\r")[0].split("\n")[0].strip().rstrip(",")
            )

            unique_products = df.drop_duplicates(subset=["clean_name"])

            # Insert products (deduplicated by cleaned name)
            seen_asins = set()
            for _, row in unique_products.iterrows():
                clean = row["clean_name"]
                asin = row["primary_asin"]
                existing = (
                    db.query(Product)
                    .filter(Product.name == clean)
                    .first()
                )
                if not existing and asin not in seen_asins:
                    new_prod = Product(
                        asin=asin,
                        name=clean,
                        description=str(row.get("categories", "")),
                        price=0.0,
                        quantity=0,
                    )
                    db.add(new_prod)
                    seen_asins.add(asin)
            db.commit()

            # Map product names to IDs (so all ASINs sharing a name resolve to one product)
            products = db.query(Product.id, Product.name).all()
            name_to_id = {p.name: p.id for p in products}

            # Insert reviews
            reviews_to_insert = []
            for _, row in df.iterrows():
                product_name = row["clean_name"]
                product_id = name_to_id.get(product_name)
                body = row["reviews.text"]

                if product_id and pd.notna(body):
                    reviews_to_insert.append(
                        Review(product_id=product_id, body=str(body))
                    )

            db.add_all(reviews_to_insert)
            db.commit()
            print("🎉 Database Initialization Completed Successfully!")
        except Exception as e:
            db.rollback()
            print(f"❌ Error populating dataset: {e}")


# Database helper functions


def get_products() -> list[dict]:
    with SessionLocal() as db:
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


def get_product(product_id: int) -> dict | None:
    with SessionLocal() as db:
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


def get_reviews(product_id: int) -> list[str]:
    with SessionLocal() as db:
        reviews = db.query(Review.body).filter(Review.product_id == product_id).all()
        return [r.body for r in reviews]


def add_review(product_id: int, review_text: str):
    with SessionLocal() as db:
        db.add(Review(product_id=product_id, body=review_text))
        db.commit()
    # Invalidate the cache since database has a new review
    clear_cache(product_id)


def get_cached_analysis(product_id: int) -> list[dict] | None:
    with SessionLocal() as db:
        cache = (
            db.query(AnalysisCache)
            .filter(AnalysisCache.product_id == product_id)
            .first()
        )
        if cache:
            try:
                return json.loads(cache.analysis)
            except Exception:
                return None
    return None


def cache_analysis(product_id: int, analysis: list[dict]):
    with SessionLocal() as db:
        cache = (
            db.query(AnalysisCache)
            .filter(AnalysisCache.product_id == product_id)
            .first()
        )
        analysis_str = json.dumps(analysis)
        if cache:
            cache.analysis = analysis_str
        else:
            db.add(AnalysisCache(product_id=product_id, analysis=analysis_str))
        db.commit()


def clear_cache(product_id: int):
    with SessionLocal() as db:
        db.query(AnalysisCache).filter(AnalysisCache.product_id == product_id).delete()
        db.commit()
