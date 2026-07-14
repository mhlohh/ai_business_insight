from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.services.analysis_service import setup
from app.api.routes import products, reviews, analyze


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize AI Core
    await setup()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(products.router)
app.include_router(reviews.router)
app.include_router(analyze.router)
