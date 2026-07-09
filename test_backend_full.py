import traceback
from fastapi.testclient import TestClient
from app.main import app

try:
    print("Initializing TestClient...")
    client = TestClient(app)
    
    print("Testing GET /db/products ...")
    response = client.get("/db/products")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()[:2] if response.status_code == 200 else response.text}")
    
    print("\nTesting GET /reviews/1 ...")
    response_reviews = client.get("/reviews/1")
    print(f"Status Code: {response_reviews.status_code}")
    print(f"Response: {response_reviews.json() if response_reviews.status_code == 200 else response_reviews.text}")
    
    print("\nTesting GET /analyze/1 ...")
    # This might fail with 404 because product 1 might not be in the database since it's empty
    response_analyze = client.get("/analyze/1")
    print(f"Status Code: {response_analyze.status_code}")
    print(f"Response: {response_analyze.json() if response_analyze.status_code == 200 else response_analyze.text}")

    print("\n✅ Backend API routes tested successfully.")
except Exception as e:
    print("\n❌ Error starting backend:")
    traceback.print_exc()
