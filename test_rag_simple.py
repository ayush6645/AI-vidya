import requests
import json
import time

def test_rag():
    print("Testing Video RAG...")
    
    # 1. Login to get token (if needed) or just hit the public/protected endpoint if we bypassed auth for testing
    # Assuming we need a token, but for RAG endpoint testing locally, do we?
    # backend/app/api/v1/endpoints/rag.py uses Depends(get_current_user_required)
    
    # Let's create a temp user or login
    base_url = "http://localhost:8080"
    
    # Login
    print("Logging in...")
    login_payload = {
        "loginType": "loginEmail",
        "login_value": "test@example.com", 
        "authType": "password",
        "auth_value": "password123"
    }
    
    # Register if not exists (ignore error or check redirect)
    # Register endpoint expects form data or json, let's use json
    reg_payload = {
        "email": "test@example.com", 
        "password": "password123", 
        "confirm_password": "password123",
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User"
    }
    reg_resp = requests.post(f"{base_url}/register", json=reg_payload)
    print(f"Register status: {reg_resp.status_code}, {reg_resp.text}")
    
    session = requests.Session()
    # Login endpoint
    resp = session.post(f"{base_url}/login", json=login_payload)
    
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        # return

    print("Login successful.")
    
    # Video RAG Request
    # Video: "User Provided" (aywZrzNaKjs)
    video_id = "aywZrzNaKjs"
    
    print(f"Chatting with video {video_id}...")
    payload = {
        "video_id": video_id,
        "question": "What is Python used for?"
    }
    
    # RAG Endpoint: /api/video-chat
    rag_resp = session.post(f"{base_url}/api/video-chat", json=payload)
    
    print(f"Status: {rag_resp.status_code}")
    if rag_resp.status_code == 200:
        print(json.dumps(rag_resp.json(), indent=2))
    else:
        print(f"Error: {rag_resp.text}")

if __name__ == "__main__":
    test_rag()
