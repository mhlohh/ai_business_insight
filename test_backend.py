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
    
    print("\n✅ Backend API routes loaded successfully.")
except Exception as e:
    print("\n❌ Error starting backend:")
    traceback.print_exc()
