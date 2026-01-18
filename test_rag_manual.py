import httpx
import asyncio
import json

async def test_rag():
    # The routes are mounted at root "/" currently based on api.py and main.py
    base_url = "http://127.0.0.1:8080"
    
    async with httpx.AsyncClient() as client:
        # 1. Register
        print("Registering Test User...")
        reg_data = {
            "email": "ragtest2@example.com", # Changed email to avoid collision if prev partial run worked
            "username": "ragtest2",
            "password": "password123",
            "confirm_password": "password123",
            "first_name": "RAG",
            "last_name": "Tester",
            "date_of_birth": "1990-01-01",
            "education": "BS CS",
            "phone_number": "1234567890"
        }
        # Path is /register
        r = await client.post(f"{base_url}/register", json=reg_data)
        print(f"Register status: {r.status_code}")
        if r.status_code not in [200, 303]:
             print(f"Register details: {r.text}")

        # 2. Login
        print("Logging in...")
        login_data = {
            "loginType": "loginUsername", 
            "login_value": "ragtest2",
            "authType": "authPassword", 
            "auth_value": "password123"
        }
        # Path is /login
        r = await client.post(f"{base_url}/login", json=login_data)
        if r.status_code != 200:
            print(f"Login Failed: {r.status_code} - {r.text}")
            return
            
        # Auth endpoint sets cookie. JSON response also has token.
        data = r.json()
        token = data.get("access_token")
        
        print(f"Got Token: {token[:10]}...")
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Request Roadmap
        # Path is /roadmap based on plans.py and api.py inclusion
        print("\nRequesting RAG Roadmap...")
        roadmap_req = {
            "topic": "Python Backend Development", 
            "level": "Beginner",
            "duration": 3
        }
        
        response = await client.post(
            f"{base_url}/roadmap", 
            json=roadmap_req, 
            headers=headers,
            timeout=120.0 
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            res_json = response.json()
            print("Generation Mode:", res_json.get("generation_mode"))
            print("Sources:", res_json.get("sources"))
            print("Response Snippet:", json.dumps(res_json, indent=2)[:500])
        else:
            print("Error:", response.text)

if __name__ == "__main__":
    asyncio.run(test_rag())
