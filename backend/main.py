from fastapi import FastAPI , HTTPException
from models import Product , AI_Insight,InsightResponse
from database import all_products,check_insights,get_raw_reviews,save_reviews

app= FastAPI()

@app.get("/products",response_model=list[Product])
async def list_product():
    products= await all_products()
    return products

@app.get("/products/{product_name}/{product_id}/insights", response_model=InsightResponse)
async def get_product_insights(product_name:str , product_id: int):
    cached_data = await check_insights(product_id)
    if cached_data:
        return {"status": "success","data": cached_data}
    raw_reviews= await get_raw_reviews(product_id)
    if not raw_reviews:
        
        raise HTTPException(status_code=404, detail="No reviews found for this product.")
    chunk_size=100
    chunks=[raw_reviews[i:i+chunk_size] for i in range(0,len(raw_reviews),chunk_size)]
    