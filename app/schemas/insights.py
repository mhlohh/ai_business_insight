from pydantic import BaseModel, Field

class Insight(BaseModel):
    insight: str = Field(description="Description of the insight")
    score: float = Field(description="Calculated priority score based on frequency and confidence", default=0.0)
    confidence: float = Field(description="Confidence level (0.0 to 1.0)", default=0.8)
    status: str = Field(description="Status string based on score (e.g. Needs Attention)", default="Needs Attention")
    frequency: float = Field(description="Frequency of occurrence across reviews", default=1)
    example_quote: str = Field(description="Representative customer quote")
    category: str = Field(description="Insight category (e.g., quality, support, price, usability, other)")

class InsightsList(BaseModel):
    insights: list[Insight] = Field(description="List of extracted business insights")
