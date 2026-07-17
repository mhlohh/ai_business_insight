from fastapi import APIRouter, HTTPException
from app.models import InsightResponse
from app.database import check_insights , save_insights , clear_insights , get_raw_reviews
from app.services.chunkers import chunkers
from app.services.model_provider import ask

router = APIRouter(prefix="/insights" ,tags=["insights"])

@router.get("/products/{product_id}", response_model=InsightResponse)

async def get_product_insights(product_id: int):
    cached_data = check_insights(product_id)
    if cached_data:
        return {"status": "success","data": cached_data}
    reviews= get_raw_reviews(product_id)
    if not reviews:
         raise HTTPException(status_code=404, detail="No reviews found for this product.")
    
    chunks = chunkers(reviews)
    
    try:
        results = await ask(chunks)
    except Exception as e:  
        raise HTTPException(status_code=500, detail="AI Engine failed to process data correctly.")

    final_response = InsightResponse(status="success", data=results)
    save_insights(product_id, final_response.model_dump())
    
    return final_response


@router.delete("/products/{product_id}")
async def clear_product_insights(product_id: int):
    deleted = clear_insights(product_id)
    if not deleted:
         raise HTTPException(status_code=404, detail="Cache not found or already cleared.")
    return {"status": "success", "message": f"Cache for product {product_id} cleared successfully."}
    
    
    
  
 

    