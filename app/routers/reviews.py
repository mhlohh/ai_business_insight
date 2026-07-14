from fastapi import APIRouter, HTTPException, Body
from app import database

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/{product_id}")
def get_product_reviews(product_id: int):
    # Returns reviews for a product in the database.
    reviews = database.get_reviews(product_id)
    return {"product_id": product_id, "reviews_count": len(reviews), "reviews": reviews}


@router.post("/{product_id}", status_code=201)
def add_product_review(product_id: int, review: str = Body(..., embed=True)):
    # Submits a new review for a product and invalidates the cached analysis.
    prod = database.get_product(product_id)
    if not prod:
        raise HTTPException(
            status_code=404, detail="Product not found in reviews database"
        )
    database.add_review(product_id, review)
    return {
        "message": "Review added successfully",
        "reviews_count": len(database.get_reviews(product_id)),
    }
