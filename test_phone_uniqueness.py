import requests
import json

BASE_URL = "http://127.0.0.1:8000"

# Test 1: Register with a new phone number
print("=== Test 1: Register with new phone ===")
response = requests.post(f"{BASE_URL}/api/accounts/register/", json={
    "username": "testuser1",
    "email": "test1@example.com",
    "password": "TestPass123!",
    "password2": "TestPass123!",
    "phone_number": "0712345678",
    "user_type": "user"
})
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}\n")

# Test 2: Try to register with same phone in different format
print("=== Test 2: Register with same phone (different format) ===")
response = requests.post(f"{BASE_URL}/api/accounts/register/", json={
    "username": "testuser2",
    "email": "test2@example.com",
    "password": "TestPass123!",
    "password2": "TestPass123!",
    "phone_number": "+254712345678",  # Same as 0712345678
    "user_type": "user"
})
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}\n")

# Test 3: Try another format
print("=== Test 3: Register with same phone (another format) ===")
response = requests.post(f"{BASE_URL}/api/accounts/register/", json={
    "username": "testuser3",
    "email": "test3@example.com",
    "password": "TestPass123!",
    "password2": "TestPass123!",
    "phone_number": "712345678",  # Same as 0712345678
    "user_type": "user"
})
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}\n")

# Test 4: Register with completely different phone
print("=== Test 4: Register with different phone ===")
response = requests.post(f"{BASE_URL}/api/accounts/register/", json={
    "username": "testuser4",
    "email": "test4@example.com",
    "password": "TestPass123!",
    "password2": "TestPass123!",
    "phone_number": "0798765432",
    "user_type": "user"
})
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}\n")
