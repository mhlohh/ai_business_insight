from fastapi import APIRouter, HTTPException
from app import database

router = APIRouter(prefix="/db", tags=["products"])

@router.get("/products")
def get_database_products():
    #Returns the list of products preloaded with Amazon reviews.
    return database.get_products()

@router.get("/product/{id}")
def get_database_product_by_id(id: int):
    #Returns a specific product from the reviews database.
    prod = database.get_product(id)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found in reviews database")
    return prod
