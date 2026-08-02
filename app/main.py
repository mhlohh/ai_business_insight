import os
import uvicorn
from fastapi import FastAPI
from app.routers import insights, products

app = FastAPI()

app.include_router(products.router)
app.include_router(insights.router)

if __name__ == "__main__":
    # Render provides the PORT environment variable (default 10000).
    # We bind to 0.0.0.0 as required by Render's web services.
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
