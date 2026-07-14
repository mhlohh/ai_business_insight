from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json
import time
from pydantic import BaseModel
from app.schemas.insights import InsightsList , Insights
from app.database import check_insights , save_insights , delete_insights , get_raw_reviews, get_product
from app.services.chunkers import chunkers
from app.services.analysis_service import ask, ask_stream

class InsightResponse(BaseModel):
    status: str
    data: Insights

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


# ==========================================
# 6. ANALYZE ROUTER (STREAMING & PIPELINE)
# ==========================================

analyze_router = APIRouter(prefix="/analyze", tags=["analyze"])


@analyze_router.get("/{product_id}")
async def analyze_product_reviews(product_id: int):
    # Analyzes a product's reviews using the parallel ADK pipeline (supports caching).
    prod = await get_product(product_id)

    if not prod:
        raise HTTPException(
            status_code=404, detail="Product not found in reviews database"
        )

    reviews = await get_raw_reviews(product_id)

    if not reviews:
        return {
            "product_id": product_id,
            "cached": False,
            "analysis": [],
            "message": "No reviews found for this product",
        }

    # Check Cache
    cached_analysis = await check_insights(product_id)

    if cached_analysis is not None:
        print(f"⚡ Cache Hit for Product {product_id}!")
        analysis_data = cached_analysis.get("analysis", cached_analysis)
        if isinstance(analysis_data, str):
            try:
                analysis_data = json.loads(analysis_data)
            except Exception:
                pass
        return {
            "product_id": product_id,
            "product_name": prod["name"],
            "cached": True,
            "reviews_analyzed": len(reviews),
            "analysis": analysis_data,
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
    await save_insights(product_id, analysis_result)

    return {
        "product_id": product_id,
        "product_name": prod["name"],
        "cached": False,
        "execution_time_seconds": round(elapsed_time, 2),
        "reviews_analyzed": len(reviews),
        "analysis": analysis_result,
    }


@analyze_router.delete("/{product_id}/cache")
async def clear_product_analysis_cache(product_id: int):
    # Clears the cached review analysis for a product.
    prod = await get_product(product_id)
    if not prod:
        raise HTTPException(
            status_code=404, detail="Product not found in reviews database"
        )
    await delete_insights(product_id)
    return {"message": f"Cache cleared successfully for product {product_id}"}


@analyze_router.get("/{product_id}/stream")
async def analyze_product_reviews_stream(product_id: int):
    # Analyzes a product's reviews and streams progress updates
    prod = await get_product(product_id)
    if not prod:
        raise HTTPException(
            status_code=404, detail="Product not found in reviews database"
        )

    reviews = await get_raw_reviews(product_id)
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
    cached_analysis = await check_insights(product_id)
    if cached_analysis is not None:
        print(f"⚡ Cache Hit for Product {product_id}!")
        analysis_data = cached_analysis.get("analysis", cached_analysis)
        if isinstance(analysis_data, str):
            try:
                analysis_data = json.loads(analysis_data)
            except Exception:
                pass
        async def cached_stream():
            yield json.dumps({
                "status": "completed",
                "cached": True,
                "reviews_analyzed": len(reviews),
                "result": analysis_data,
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
                    await save_insights(product_id, event["result"])
                yield json.dumps(event) + "\n"
        except Exception as e:
            yield json.dumps({"status": "error", "message": str(e)}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")
    
    
    
  
 

    