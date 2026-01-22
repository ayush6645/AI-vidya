import os
import requests
import json
import base64
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8080/api/tts"
OUTPUT_DIR = "test_output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def test_health():
    print("\n1. Testing Health Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print("❌ Health check failed")
    except Exception as e:
        print(f"❌ Health check error: {e}")

def test_simple():
    print("\n2. Testing Simple Endpoint...")
    output_file = os.path.join(OUTPUT_DIR, "simple_test.mp3")
    try:
        response = requests.get(f"{BASE_URL}/simple-test")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200 and response.headers['content-type'] == 'audio/mpeg':
            with open(output_file, "wb") as f:
                f.write(response.content)
            print(f"✅ Simple test passed. Saved to {output_file}")
            print(f"Size: {len(response.content)} bytes")
        else:
            print(f"❌ Simple test failed. Content-Type: {response.headers.get('content-type')}")
            print(f"Content: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Simple test error: {e}")

def test_speak():
    print("\n3. Testing Speak Endpoint (POST)...")
    output_file = os.path.join(OUTPUT_DIR, "speak_test.mp3")
    payload = {
        "text": "Hello, this is a test of the simplified text to speech service.",
        "gender": "FEMALE",
        "speed": 1.0
    }
    
    try:
        response = requests.post(f"{BASE_URL}/speak", json=payload)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200 and response.headers['content-type'] == 'audio/mpeg':
            with open(output_file, "wb") as f:
                f.write(response.content)
            print(f"✅ Speak test passed. Saved to {output_file}")
            print(f"Size: {len(response.content)} bytes")
        else:
            print(f"❌ Speak test failed. Content-Type: {response.headers.get('content-type')}")
            print(f"Content: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Speak test error: {e}")

if __name__ == "__main__":
    test_health()
    test_simple()
    test_speak()
