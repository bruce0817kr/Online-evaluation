import requests

BACKEND_URL = "http://localhost:8080"

def test_health():
    try:
        r = requests.get(f"{BACKEND_URL}/health")
        print(f"Basic health: {r.status_code}")
        
        r2 = requests.get(f"{BACKEND_URL}/api/health/detailed")
        print(f"Detailed health: {r2.status_code}")
        
        r3 = requests.get(f"{BACKEND_URL}/api/health/liveness")
        print(f"Liveness: {r3.status_code}")
        
        r4 = requests.get(f"{BACKEND_URL}/api/health/readiness")
        print(f"Readiness: {r4.status_code}")
        
        r5 = requests.get(f"{BACKEND_URL}/api/status")
        print(f"API Status: {r5.status_code}")
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_health()
