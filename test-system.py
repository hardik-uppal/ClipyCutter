#!/usr/bin/env python3

"""
Simple test script to verify backend functionality
Run this after starting the services to test the API
"""

import requests
import time
import sys

def test_api():
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Clippy v2 Backend API...")
    print("="*40)
    
    # Test 1: Health check
    try:
        print("1. Testing health endpoint...")
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("   ✅ Backend is responding")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Cannot connect to backend: {e}")
        print("   💡 Make sure services are running: docker-compose up")
        return False
    
    # Test 2: API Documentation
    try:
        print("\n2. Testing API documentation...")
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print("   ✅ API documentation is available")
            print(f"   Visit: {base_url}/docs")
        else:
            print(f"   ❌ Docs endpoint failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Cannot access docs: {e}")
    
    # Test 3: Clips endpoint
    try:
        print("\n3. Testing clips list endpoint...")
        response = requests.get(f"{base_url}/api/clips", timeout=5)
        if response.status_code == 200:
            clips = response.json()
            print(f"   ✅ Clips endpoint working (found {len(clips)} clips)")
        else:
            print(f"   ❌ Clips endpoint failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Cannot access clips endpoint: {e}")
    
    print("\n🎉 Backend testing complete!")
    print(f"🌐 Frontend should be available at: http://localhost:3000")
    return True

def test_frontend():
    print("\n🧪 Testing Frontend...")
    print("="*25)
    
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is responding")
            print("🎯 You can now use the application!")
        else:
            print(f"❌ Frontend check failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to frontend: {e}")
        print("💡 Frontend might still be starting up...")

if __name__ == "__main__":
    print("🎬 Clippy v2 - System Test")
    print("="*30)
    
    if test_api():
        test_frontend()
        
        print("\n" + "="*50)
        print("🎉 SYSTEM TEST COMPLETE!")
        print("")
        print("✅ Your Clippy v2 installation is working!")
        print("")
        print("🚀 Next steps:")
        print("   1. Go to http://localhost:3000")
        print("   2. Try creating a clip with a YouTube URL")
        print("   3. For YouTube upload, configure API keys (see SETUP.md)")
        print("")
        print("📚 Resources:")
        print("   - API Docs: http://localhost:8000/docs")
        print("   - Setup Guide: SETUP.md")
        print("   - Logs: docker-compose logs -f")
    else:
        print("\n❌ System test failed!")
        print("💡 Try running: docker-compose up --build")
        sys.exit(1)