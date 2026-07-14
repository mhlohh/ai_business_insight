from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.services.analysis_service import setup
from app.routers import insights, products, reviews


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize AI Core
    await setup()
    yield


app = FastAPI(lifespan=lifespan)

# Team's routers
app.include_router(products.router)
app.include_router(insights.router)

# User's API routes (now in app/routers)
app.include_router(products.db_router)
app.include_router(reviews.router)
app.include_router(insights.analyze_router)
