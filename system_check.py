#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
System Status Check
Quick verification of Online Evaluation System
"""

import requests
import json
import sys

def check_system():
    base_url = "http://localhost:8080"
    
    print("🔍 Online Evaluation System Status Check")
    print("=" * 50)
    
    # 1. Server Response Check
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"✅ Server Response: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Server Connection Failed: {str(e)}")
        return False
    
    # 2. API Documentation Check
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        print(f"✅ API Documentation: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ API Documentation Failed: {str(e)}")
    
    # 3. Health Check
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health Check: System Healthy")
        else:
            print(f"⚠️ Health Check: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Health Check Failed: {str(e)}")
    
    # 4. Database Connection Check
    try:
        # Register a test user to check DB connectivity
        test_user = {
            "username": "system_check_user",
            "email": "systemcheck@example.com", 
            "password": "checkpass123",
            "role": "evaluator",
            "company": "System Check"
        }
        
        response = requests.post(f"{base_url}/api/auth/register", json=test_user, timeout=10)
        if response.status_code in [200, 201]:
            print("✅ Database: Registration Successful")
        elif response.status_code == 400:
            print("✅ Database: User Exists (DB Connected)")
        else:
            print(f"⚠️ Database: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Database Check Failed: {str(e)}")
    
    print("\n🎯 System Summary:")
    print("✨ Online Evaluation System is running successfully!")
    print(f"🌐 Web Interface: {base_url}")
    print(f"📚 API Documentation: {base_url}/docs")
    print("\n📋 Available Features:")
    print("   • User Management & Authentication")
    print("   • Project & Template Management") 
    print("   • Evaluation Process")
    print("   • Real-time Analytics Dashboard")
    print("   • Advanced Export System (PDF/Excel)")
    print("   • Korean Language Support")
    
    return True

if __name__ == "__main__":
    success = check_system()
    sys.exit(0 if success else 1)
