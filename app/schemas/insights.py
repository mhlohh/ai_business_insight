from pydantic import BaseModel, Field

VALID_CATEGORIES = {"quality", "support", "price", "usability", "other"}

# Defined here so Python can handle the math reliably
CATEGORY_WEIGHTS = {
    "quality": 1.5,
    "support": 1.2,
    "price": 1.0,
    "usability": 1.3,
    "other": 1.0,
}


class Insights(BaseModel):
    """
    Schema used to validate and sanitize the LLM output.
    """

    insight: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    frequency: int = Field(..., gt=0)
    example_quote: str
    category: str


class InsightsList(BaseModel):
    insights: list[Insights] = Field(description="List of extracted business insights")
