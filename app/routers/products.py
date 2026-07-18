from fastapi import APIRouter, HTTPException
from app.schemas.database_schema import ProductResponse
from app.database import get_products

router = APIRouter(prefix="/products" ,tags=["products"])
@router.get("/",response_model = list[ProductResponse])
def get_all_products():
    products = get_products()
    if not products:
        raise HTTPException(status_code=404, detail="No products found ")
    return products

    