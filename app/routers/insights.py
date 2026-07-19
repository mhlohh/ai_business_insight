from fastapi import APIRouter, HTTPException
from app.schemas.insights import InsightsList
from app.database import (
    get_cached_analysis,
    cache_analysis,
    clear_cache,
    get_reviews,
)
from app.services.chunkers import chunkers
from app.services.analysis_service import ask

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/products/{product_id}", response_model=InsightsList)   
def get_cached_analysis(product_id: int):
    cached_data = get_cached_analysis(product_id)
    if cached_data:
        return {"status": "success", "data": cached_data}
    reviews = get_reviews(product_id)
    if not reviews:
        raise HTTPException(
            status_code=404, detail="No reviews found for this product."
        )

    chunks = chunkers(reviews)

    try:
        results = ask(chunks)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="AI Engine failed to process data correctly."
        )

    cache_analysis(product_id, results.model_dump())

    return results


@router.delete("/products/{product_id}")
def clear_product_insights(product_id: int):
    deleted = clear_cache(product_id)
    if not deleted:
        raise HTTPException(
            status_code=404, detail="Cache not found or already cleared."
        )
    return {
        "status": "success",
        "message": f"Cache for product {product_id} cleared successfully.",
    }
