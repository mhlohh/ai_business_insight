from fastapi import APIRouter, HTTPException, Body
from app import database

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/{product_id}")
async def get_product_reviews(product_id: int):
    # Returns reviews for a product in the database.
    reviews = await database.get_raw_reviews(product_id)
    return {"product_id": product_id, "reviews_count": len(reviews), "reviews": reviews}


@router.post("/{product_id}", status_code=201)
async def add_product_review(product_id: int, review: str = Body(..., embed=True)):
    # Submits a new review for a product and invalidates the cached analysis.
    prod = await database.get_product(product_id)
    if not prod:
        raise HTTPException(
            status_code=404, detail="Product not found in reviews database"
        )
    await database.add_review(product_id, review)
    return {
        "message": "Review added successfully",
        "reviews_count": len(await database.get_raw_reviews(product_id)),
    }
