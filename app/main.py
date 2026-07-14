from fastapi import FastAPI
from app.routers import insights, products

app = FastAPI()

app.include_router(products.router)
app.include_router(insights.router)
