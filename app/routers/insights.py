from fastapi import APIRouter, HTTPException
from app.models import AI_Insight,InsightsList
from app.database import check_insights , clear_insights , get_raw_reviews
from app.services.chunkers import chunkers
from app.services.model_provider import ask
from app.logger import logger

router = APIRouter(prefix="/insights" ,tags=["insights"])

@router.get("/products/{product_id}", response_model=InsightsList)

async def get_product_insights(product_id: int):
    logger.info(f"API GET /insights/products/{product_id} - Fetching insights")
    cached_data = check_insights(product_id)
    if cached_data:
        logger.info(f"API GET /insights/products/{product_id} - Cache hit")
        return {"status": "success","data": cached_data}
    
    logger.info(f"API GET /insights/products/{product_id} - Cache miss. Retrieving reviews.")
    reviews= get_raw_reviews(product_id)
    if not reviews:
         logger.warning(f"API GET /insights/products/{product_id} - No reviews found")
         raise HTTPException(status_code=404, detail="No reviews found for this product.")
    
    logger.info(f"API GET /insights/products/{product_id} - Found {len(reviews)} reviews. Chunking.")
    chunks = chunkers(reviews)
    
    try:
        logger.info(f"API GET /insights/products/{product_id} - Calling AI ask function with {len(chunks)} chunks")
        results = await ask(chunks)
        logger.info(f"API GET /insights/products/{product_id} - AI ask function succeeded")
    except Exception as e:  
        logger.error(f"API GET /insights/products/{product_id} - AI Engine failed: {e}")
        raise HTTPException(status_code=500, detail="AI Engine failed to process data correctly.")

    return results


@router.delete("/products/{product_id}")
async def clear_product_insights(product_id: int):
    logger.info(f"API DELETE /insights/products/{product_id} - Clearing cache")
    deleted = clear_insights(product_id)
    if not deleted:
         logger.warning(f"API DELETE /insights/products/{product_id} - Cache not found to clear")
         raise HTTPException(status_code=404, detail="Cache not found or already cleared.")
    logger.info(f"API DELETE /insights/products/{product_id} - Cache cleared successfully")
    return {"status": "success", "message": f"Cache for product {product_id} cleared successfully."}
    
    
    
  
 

    