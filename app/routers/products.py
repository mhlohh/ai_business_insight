from fastapi import APIRouter, HTTPException
from app.models import Product
from app.database import all_products
from app.logger import logger

router = APIRouter(prefix="/products" ,tags=["products"])
@router.get("/")
def  get_all_products():
    logger.info("API GET /products/ - Fetching all products list")
    products = all_products()
    if not products:
        logger.warning("API GET /products/ - No products found in database")
        raise HTTPException(status_code=404, detail="No products found ")
    logger.info(f"API GET /products/ - Successfully returned {len(products)} products")
    return products
    