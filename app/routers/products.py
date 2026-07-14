from fastapi import APIRouter, HTTPException
from app.schemas.Database_schema import Product
from app.database import all_products

router = APIRouter(prefix="/products" ,tags=["products"])
@router.get("/")
async def  get_all_products():
    products = await all_products()
    if not products:
        raise HTTPException(status_code=404, detail="No products found ")
    return products
    