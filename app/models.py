from pydantic import BaseModel

class Product(BaseModel):
    product_id: int
    name: str

  
class AI_Insight(BaseModel):
    insight: str
    score: float
    status: str
    frequency: int
    example_quote: str
    category: str
    confidence: float

class InsightResponse(BaseModel):
    status: str    
    insight: str
    category: str
    example_quote: str
    frequency: int
    score: float
    

