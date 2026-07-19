from pydantic import BaseModel, Field


class Product(BaseModel):
    id: int
    name: str
    description: str


class Insight(BaseModel):
    insight: str = Field(description="Description of the insight")
    confidence: float = Field(description="Confidence level (0.0 to 1.0)", default=0.8)
    frequency: float = Field(
        description="Frequency of occurrence across reviews", default=1
    )
    example_quote: str = Field(description="Representative customer quote")
    category: str = Field(
        description="Insight category (e.g., quality, support, price, usability, other)"
    )
    score: float | None = Field(
        description="Calculated score based on frequency, confidence, and category",
        default=None,
    )


class InsightsList(BaseModel):
    insights: list[Insight] = Field(description="List of extracted business insights")
