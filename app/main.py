import os
import uvicorn
from fastapi import FastAPI
from app.routers import insights, products

app = FastAPI()

app.include_router(products.router)
app.include_router(insights.router)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
