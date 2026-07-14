from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app import database
from app.services.analysis_service import ask, ask_stream
import time
import json

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


@router.get("/{product_id}/stream")
async def analyze_product_reviews_stream(product_id: int):
    # Analyzes a product's reviews and streams progress updates
    prod = database.get_product(product_id)
    if not prod:
        raise HTTPException(
            status_code=404, detail="Product not found in reviews database"
        )

    reviews = database.get_reviews(product_id)
    if not reviews:
        async def empty_stream():
            yield json.dumps({
                "status": "completed",
                "cached": False,
                "result": [],
                "message": "No reviews found for this product",
                "reviews_analyzed": 0,
                "execution_time_seconds": 0
            }) + "\n"
        return StreamingResponse(empty_stream(), media_type="application/x-ndjson")

    # Check Cache
    cached_analysis = database.get_cached_analysis(product_id)
    if cached_analysis is not None:
        print(f"⚡ Cache Hit for Product {product_id}!")
        async def cached_stream():
            yield json.dumps({
                "status": "completed",
                "cached": True,
                "reviews_analyzed": len(reviews),
                "result": cached_analysis,
                "execution_time_seconds": 0
            }) + "\n"
        return StreamingResponse(cached_stream(), media_type="application/x-ndjson")

    print(
        f"🤖 Cache Miss for Product {product_id}! Running parallel analysis pipeline (Streaming)..."
    )
    reviews_prompt = "\n".join([f"- {r}" for r in reviews])

    async def event_generator():
        start_time = time.time()
        try:
            async for event in ask_stream(reviews_prompt):
                if event["status"] == "completed":
                    elapsed_time = time.time() - start_time
                    event["execution_time_seconds"] = round(elapsed_time, 2)
                    event["reviews_analyzed"] = len(reviews)
                    event["cached"] = False
                    # Store in cache
                    database.cache_analysis(product_id, event["result"])
                yield json.dumps(event) + "\n"
        except Exception as e:
            yield json.dumps({"status": "error", "message": str(e)}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")
