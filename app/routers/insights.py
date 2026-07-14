from fastapi import APIRouter, HTTPException
from schemas.insights import InsightsList , Insights
from app.database import check_insights , save_insights , delete_insights , get_raw_reviews
from services.chunkers import chunkers
from app.services.analysis_service import ask

router = APIRouter(prefix="/insights" ,tags=["insights"])

@router.get("/products/{product_name}/{product_id}", response_model=InsightsList)

async def get_product_insights(product_name:str , product_id: int):
    cached_data = await check_insights(product_id)
    if cached_data:
        return {"status": "success","data": cached_data}
    reviews= await get_raw_reviews(product_id)
    if not reviews:
         raise HTTPException(status_code=404, detail="No reviews found for this product.")
    
    chunks = chunkers(reviews)
    
    try:
        results = await ask(chunks)
        validated_insight = Insights(**results) 
    except Exception as e:
        raise HTTPException(status_code=500, detail="AI Engine failed to process data correctly.")

    final_response = InsightResponse(status="success", data=validated_insight)
    await save_insights(product_id, final_response.model_dump())
    
    return final_response


@router.delete("/products/{product_name}/{product_id}")
async def clear_product_insights(product_name: str, product_id: int):
    deleted = await delete_insights(product_id)
    if not deleted:
         raise HTTPException(status_code=404, detail="Cache not found or already cleared.")
    return {"status": "success", "message": f"Cache for product {product_id} cleared successfully."}
    
    
    
  
 

    