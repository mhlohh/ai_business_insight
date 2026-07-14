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

# Register unified routers
app.include_router(products.router)
app.include_router(insights.router)
app.include_router(reviews.router)
