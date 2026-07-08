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

class InsightResponse(BaseModel):
    status: str    
    data: AI_Insight 

