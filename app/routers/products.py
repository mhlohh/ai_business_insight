from fastapi import APIRouter, HTTPException
from app.schemas.Database_schema import Product
from app.database import get_products, get_product


async def all_products():
    return get_products()


router = APIRouter(prefix="/products" ,tags=["products"])
db_router = APIRouter(prefix="/db", tags=["products"])


@router.get("/")
async def  get_all_products():
    products = await all_products()
    if not products:
        raise HTTPException(status_code=404, detail="No products found ")
    return products


@db_router.get("/products")
def get_database_products():
    # Returns the list of products preloaded with Amazon reviews.
    return get_products()


@db_router.get("/product/{id}")
def get_database_product_by_id(id: int):
    # Returns a specific product from the reviews database.
    prod = get_product(id)
    if not prod:
        raise HTTPException(
            status_code=404, detail="Product not found in reviews database"
        )
    return prod
