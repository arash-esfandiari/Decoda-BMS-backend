
import sys
import os
import asyncio
from fastapi.testclient import TestClient

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)

def test_endpoint(endpoint):
    print(f"\n--- Testing {endpoint} ---")
    try:
        response = client.get(endpoint)
        print(f"Status Code: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
        else:
            # Try to parse json to ensure it's valid
            data = response.json()
            print(f"Success. Total items: {data.get('total', 'N/A')}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_endpoint("/patients/")
    test_endpoint("/appointments/")
    test_endpoint("/services/")
    test_endpoint("/providers/")
