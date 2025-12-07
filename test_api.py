"""
Test script for BaghChal backend API
Run this to verify all endpoints are working
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_register_and_login():
    """Test user registration and login"""
    print("\n=== Testing Authentication ===")
    
    # Register
    username = f"testuser_{int(time.time())}"
    password = "testpass123"
    
    register_data = {
        "username": username,
        "password": password
    }
    
    print(f"Registering user: {username}")
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    print(f"Register Status: {response.status_code}")
    print(f"Register Response: {response.json()}")
    
    if response.status_code != 200:
        return None, None
    
    register_result = response.json()
    token = register_result.get("token")
    user_id = register_result.get("userId")
    
    # Login
    print(f"\nLogging in user: {username}")
    login_data = {
        "username": username,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Login Status: {response.status_code}")
    print(f"Login Response: {response.json()}")
    
    return token, user_id

def test_matchmaking(token):
    """Test matchmaking"""
    print("\n=== Testing Matchmaking ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print("Starting matchmaking...")
    response = requests.post(f"{BASE_URL}/matchmaking/start", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    return response.json()

def test_community(token):
    """Test community endpoints"""
    print("\n=== Testing Community ===")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Create post
    post_data = {
        "title": "Test Post",
        "content": "This is a test post from the API test script!"
    }
    
    print("Creating community post...")
    response = requests.post(f"{BASE_URL}/community/post", json=post_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Get feed
    print("\nGetting community feed...")
    response = requests.get(f"{BASE_URL}/community/feed")
    print(f"Status: {response.status_code}")
    print(f"Feed items: {len(response.json())}")
    
    return response.status_code == 200

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("BaghChal Backend API Test Suite")
    print("=" * 60)
    
    # Test health
    if not test_health():
        print("\n❌ Health check failed! Is the server running?")
        return
    
    print("\n✅ Health check passed")
    
    # Test auth
    token, user_id = test_register_and_login()
    if not token:
        print("\n❌ Authentication failed!")
        return
    
    print(f"\n✅ Authentication passed (User ID: {user_id})")
    
    # Test matchmaking
    match_result = test_matchmaking(token)
    print("\n✅ Matchmaking test completed")
    
    # Test community
    if test_community(token):
        print("\n✅ Community test passed")
    else:
        print("\n⚠️ Community test had issues")
    
    print("\n" + "=" * 60)
    print("Test Suite Complete!")
    print("=" * 60)
    print("\n📝 Next steps:")
    print("1. Open http://localhost:8000/tests/static_test_ui.html")
    print("2. Test the full game flow with WebSockets")
    print("3. Open two browser tabs to play against yourself")

if __name__ == "__main__":
    try:
        run_all_tests()
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to server!")
        print("Make sure the server is running on http://localhost:8000")
        print("Run: python main.py")
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
