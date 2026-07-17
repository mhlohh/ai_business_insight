from fastapi import FastAPI
from app.routers import insights ,products

app = FastAPI()

app.include_router(products.routers)
app.include_router(insights.routers)