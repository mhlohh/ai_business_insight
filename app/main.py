from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.services.analysis_service import setup
from app.routers import insights as team_insights, products as team_products
from app.api.routes import products as api_products, reviews as api_reviews, analyze as api_analyze


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize AI Core
    await setup()
    yield


app = FastAPI(lifespan=lifespan)

# Team's routers
app.include_router(team_products.router)
app.include_router(team_insights.router)

# User's API routes
app.include_router(api_products.router)
app.include_router(api_reviews.router)
app.include_router(api_analyze.router)
