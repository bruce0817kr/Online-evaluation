#!/usr/bin/env python3
"""
Test script for the export API endpoints
"""
import requests
import json
import os
import time

# Configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

# Test credentials (you'll need to update these based on your system)
TEST_USER = {
    "email": "admin@test.com",
    "password": "admin123"
}

def test_login():
    """Test login and get authentication token"""
    print("🔐 Testing login...")
    
    login_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }
    
    try:
        response = requests.post(f"{API_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"✅ Login successful! Token: {token[:20]}...")
            return token
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_export_list(token):
    """Test the export list endpoint"""
    print("\n📋 Testing export list endpoint...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_URL}/evaluations/export-list", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Export list retrieved! Found {len(data)} evaluations")
            for eval_data in data[:3]:  # Show first 3
                print(f"   - {eval_data.get('company_name', 'Unknown')} | {eval_data.get('template_name', 'Unknown')}")
            return data
        else:
            print(f"❌ Export list failed: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"❌ Export list error: {e}")
        return []

def test_single_export(token, evaluation_id, format_type):
    """Test single evaluation export"""
    print(f"\n📄 Testing single export (ID: {evaluation_id}, Format: {format_type})...")
    
    headers = {"Authorization": f"Bearer {token}"}
    params = {"format": format_type}
    
    try:
        response = requests.get(
            f"{API_URL}/evaluations/{evaluation_id}/export", 
            headers=headers, 
            params=params
        )
        
        if response.status_code == 200:
            # Check if it's a file download
            content_type = response.headers.get('content-type', '')
            content_disposition = response.headers.get('content-disposition', '')
            
            print(f"✅ Single export successful!")
            print(f"   Content-Type: {content_type}")
            print(f"   Content-Disposition: {content_disposition}")
            print(f"   Response size: {len(response.content)} bytes")
            
            # Save file for verification
            filename = f"test_export_{evaluation_id}_{format_type}.{'pdf' if format_type == 'pdf' else 'xlsx'}"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"   File saved as: {filename}")
            
            return True
        else:
            print(f"❌ Single export failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Single export error: {e}")
        return False

def test_bulk_export(token):
    """Test bulk export functionality"""
    print(f"\n📊 Testing bulk export...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get projects first
    try:
        projects_response = requests.get(f"{API_URL}/projects", headers=headers)
        if projects_response.status_code != 200:
            print("❌ Could not fetch projects for bulk export test")
            return False
            
        projects = projects_response.json()
        if not projects:
            print("❌ No projects found for bulk export test")
            return False
            
        project_id = projects[0]["id"]
        print(f"   Using project: {projects[0]['name']} (ID: {project_id})")
        
        # Test bulk export
        bulk_data = {
            "project_id": project_id,
            "format": "excel",
            "export_type": "combined"
        }
        
        response = requests.post(
            f"{API_URL}/evaluations/bulk-export", 
            headers=headers, 
            json=bulk_data
        )
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            content_disposition = response.headers.get('content-disposition', '')
            
            print(f"✅ Bulk export successful!")
            print(f"   Content-Type: {content_type}")
            print(f"   Content-Disposition: {content_disposition}")
            print(f"   Response size: {len(response.content)} bytes")
            
            # Save file for verification
            filename = f"test_bulk_export_{int(time.time())}.{'zip' if 'zip' in content_type else 'xlsx'}"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"   File saved as: {filename}")
            
            return True
        else:
            print(f"❌ Bulk export failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Bulk export error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Export API Tests")
    print("=" * 50)
    
    # Test login
    token = test_login()
    if not token:
        print("❌ Cannot continue without authentication token")
        return
    
    # Test export list
    evaluations = test_export_list(token)
    
    # Test single export if we have evaluations
    if evaluations:
        evaluation_id = evaluations[0]["id"]
        
        # Test PDF export
        test_single_export(token, evaluation_id, "pdf")
        
        # Test Excel export
        test_single_export(token, evaluation_id, "excel")
    else:
        print("⚠️  No evaluations found for single export test")
    
    # Test bulk export
    test_bulk_export(token)
    
    print("\n" + "=" * 50)
    print("🏁 Export API Tests Complete!")

if __name__ == "__main__":
    main()
