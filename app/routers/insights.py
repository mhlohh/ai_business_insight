import json
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from app.schemas.insights import InsightsList, Insights
from app.database import get_cached_analysis, cache_analysis, clear_cache, get_reviews
from app.services.chunkers import chunkers
from app.services.analysis_service import ask


class InsightResponse(BaseModel):
    status: str
    data: Insights


async def check_insights(product_id: int):
    res = get_cached_analysis(product_id)
    if res is not None:
        return {"analysis": json.dumps(res)}
    return None


async def save_insights(product_id: int, insight_data):
    if isinstance(insight_data, str):
        try:
            insight_data = json.loads(insight_data)
        except Exception:
            pass
    if isinstance(insight_data, dict) and "data" in insight_data:
        analysis_data = insight_data["data"]
    else:
        analysis_data = insight_data
    cache_analysis(product_id, analysis_data)


async def delete_insights(product_id: int):
    existing = get_cached_analysis(product_id)
    if existing is None:
        return False
    clear_cache(product_id)
    return True


async def get_raw_reviews(product_id: int):
    return get_reviews(product_id)


router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/products/{product_name}/{product_id}", response_model=InsightsList)
async def get_product_insights(product_name: str, product_id: int):
    cached_data = await check_insights(product_id)
    if cached_data:
        return {"status": "success", "data": cached_data}
    reviews = await get_raw_reviews(product_id)
    if not reviews:
        raise HTTPException(
            status_code=404, detail="No reviews found for this product."
        )

    chunks = chunkers(reviews)

    try:
        results = await ask(chunks)
        validated_insight = Insights(**results)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="AI Engine failed to process data correctly."
        )

    final_response = InsightResponse(status="success", data=validated_insight)
    await save_insights(product_id, final_response.model_dump())

    return final_response


@router.delete("/products/{product_name}/{product_id}")
async def clear_product_insights(product_name: str, product_id: int):
    deleted = await delete_insights(product_id)
    if not deleted:
        raise HTTPException(
            status_code=404, detail="Cache not found or already cleared."
        )
    return {
        "status": "success",
        "message": f"Cache for product {product_id} cleared successfully.",
    }
