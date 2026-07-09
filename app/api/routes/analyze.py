from fastapi import APIRouter, HTTPException
from app import database
from app.services.analysis_service import ask
import time

router = APIRouter(prefix="/analyze", tags=["analyze"])


@router.get("/{product_id}")
async def analyze_product_reviews(product_id: int):
    # Analyzes a product's reviews using the parallel ADK pipeline (supports caching).
    prod = database.get_product(product_id)

    if not prod:
        raise HTTPException(
            status_code=404, detail="Product not found in reviews database"
        )

    reviews = database.get_reviews(product_id)

    if not reviews:
        return {
            "product_id": product_id,
            "cached": False,
            "analysis": [],
            "message": "No reviews found for this product",
        }

    # Check Cache
    cached_analysis = database.get_cached_analysis(product_id)

    if cached_analysis is not None:
        print(f"⚡ Cache Hit for Product {product_id}!")
        return {
            "product_id": product_id,
            "product_name": prod["name"],
            "cached": True,
            "reviews_analyzed": len(reviews),
            "analysis": cached_analysis,
        }

    print(
        f"🤖 Cache Miss for Product {product_id}! Running parallel analysis pipeline..."
    )
    # Join reviews into a single text prompt
    reviews_prompt = "\n".join([f"- {r}" for r in reviews])

    start_time = time.time()
    analysis_result = await ask(reviews_prompt)
    elapsed_time = time.time() - start_time

    # Store in cache
    database.cache_analysis(product_id, analysis_result)

    return {
        "product_id": product_id,
        "product_name": prod["name"],
        "cached": False,
        "execution_time_seconds": round(elapsed_time, 2),
        "reviews_analyzed": len(reviews),
        "analysis": analysis_result,
    }


@router.delete("/{product_id}/cache")
def clear_product_analysis_cache(product_id: int):
    # Clears the cached review analysis for a product.
    prod = database.get_product(product_id)
    if not prod:
        raise HTTPException(
            status_code=404, detail="Product not found in reviews database"
        )
    database.clear_cache(product_id)
    return {"message": f"Cache cleared successfully for product {product_id}"}
