from pydantic import BaseModel

class Product(BaseModel):
    product_id: int
    name: str

  
class AI_Insight(BaseModel):
    summary: str
    pros: list[str]
    cons: list[str]

class InsightResponse(BaseModel):
    status: str    
    data: AI_Insight 

