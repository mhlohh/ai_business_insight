from fastapi import APIRouter, HTTPException
from app.schemas.Database_schema import Product
from app.database import all_products, get_product

router = APIRouter(tags=["products"])

@router.get("/products")
async def  get_all_products():
    products = await all_products()
    if not products:
        raise HTTPException(status_code=404, detail="No products found ")
    return products


@router.get("/db/products")
async def get_database_products():
    # Returns the list of products preloaded with Amazon reviews.
    return await all_products()


@router.get("/db/product/{id}")
async def get_database_product_by_id(id: int):
    # Returns a specific product from the reviews database.
    prod = await get_product(id)
    if not prod:
        raise HTTPException(
            status_code=404, detail="Product not found in reviews database"
        )
    return prod
    