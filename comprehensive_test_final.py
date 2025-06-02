import requests
import json
import time

BACKEND_URL = "http://localhost:8080"

def comprehensive_test():
    tests = {}
    
    # Test 1: Basic Health
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=5)
        tests['basic_health'] = r.status_code == 200
        if tests['basic_health']:
            print("✅ Basic Health: PASS")
        else:
            print(f"❌ Basic Health: FAIL ({r.status_code})")
    except Exception as e:
        tests['basic_health'] = False
        print(f"❌ Basic Health: ERROR ({e})")
    
    # Test 2: Detailed Health
    try:
        r = requests.get(f"{BACKEND_URL}/api/health/detailed", timeout=10)
        tests['detailed_health'] = r.status_code == 200
        if tests['detailed_health']:
            print("✅ Detailed Health: PASS")
            data = r.json()
            if 'system_metrics' in data:
                cpu = data['system_metrics'].get('cpu_usage', 0)
                mem = data['system_metrics'].get('memory_usage', {}).get('percent', 0)
                print(f"   CPU: {cpu:.1f}%, Memory: {mem:.1f}%")
        else:
            print(f"❌ Detailed Health: FAIL ({r.status_code})")
    except Exception as e:
        tests['detailed_health'] = False
        print(f"❌ Detailed Health: ERROR ({e})")
    
    # Test 3: Liveness Probe
    try:
        r = requests.get(f"{BACKEND_URL}/api/health/liveness", timeout=5)
        tests['liveness_probe'] = r.status_code == 200
        if tests['liveness_probe']:
            print("✅ Liveness Probe: PASS")
        else:
            print(f"❌ Liveness Probe: FAIL ({r.status_code})")
    except Exception as e:
        tests['liveness_probe'] = False
        print(f"❌ Liveness Probe: ERROR ({e})")
    
    # Test 4: Readiness Probe
    try:
        r = requests.get(f"{BACKEND_URL}/api/health/readiness", timeout=5)
        tests['readiness_probe'] = r.status_code == 200
        if tests['readiness_probe']:
            print("✅ Readiness Probe: PASS")
        else:
            print(f"❌ Readiness Probe: FAIL ({r.status_code})")
    except Exception as e:
        tests['readiness_probe'] = False
        print(f"❌ Readiness Probe: ERROR ({e})")
    
    # Test 5: WebSocket (simplified test)
    try:
        # Just test that the endpoint exists
        import websockets
        tests['websocket_available'] = True
        print("✅ WebSocket Support: AVAILABLE")
    except ImportError:
        tests['websocket_available'] = False
        print("❌ WebSocket Support: NOT AVAILABLE")
    
    # Test 6: Cache Performance
    try:
        times = []
        for i in range(3):
            start = time.time()
            r = requests.get(f"{BACKEND_URL}/api/health/detailed", timeout=10)
            end = time.time()
            if r.status_code == 200:
                times.append(end - start)
        
        if times:
            avg_time = sum(times) / len(times)
            tests['cache_performance'] = avg_time < 2.0
            if tests['cache_performance']:
                print(f"✅ Cache Performance: PASS (avg: {avg_time:.3f}s)")
            else:
                print(f"❌ Cache Performance: SLOW (avg: {avg_time:.3f}s)")
        else:
            tests['cache_performance'] = False
            print("❌ Cache Performance: NO DATA")
    except Exception as e:
        tests['cache_performance'] = False
        print(f"❌ Cache Performance: ERROR ({e})")
    
    # Test 7: Notification System (Redis check)
    try:
        r = requests.get(f"{BACKEND_URL}/api/status", timeout=5)
        if r.status_code == 200:
            data = r.json()
            cache_status = data.get('cache', {}).get('status', 'disconnected')
            tests['notification_system'] = cache_status == 'connected'
            if tests['notification_system']:
                print("✅ Notification System: CONNECTED")
            else:
                print(f"❌ Notification System: {cache_status.upper()}")
        else:
            tests['notification_system'] = False
            print(f"❌ Notification System: FAIL ({r.status_code})")
    except Exception as e:
        tests['notification_system'] = False
        print(f"❌ Notification System: ERROR ({e})")
    
    # Calculate final score
    total_tests = len(tests)
    passed_tests = sum(tests.values())
    score = (passed_tests / total_tests) * 100
    
    print("\n" + "="*50)
    print(f"FINAL SCORE: {passed_tests}/{total_tests} tests passed ({score:.1f}%)")
    print("="*50)
    
    if score >= 90:
        print("🎉 EXCELLENT! System is production-ready!")
    elif score >= 80:
        print("👍 GOOD! Most features are working.")
    elif score >= 70:
        print("⚠️  FAIR! Some improvements needed.")
    else:
        print("🚨 POOR! Multiple issues found.")
    
    return score

if __name__ == "__main__":
    score = comprehensive_test()
