import asyncio
import os
from dotenv import load_dotenv
from backend.app.services.tts_service import tts_service

load_dotenv()

async def test_elevenlabs():
    print("Testing ElevenLabs TTS Integration...")
    try:
        text = "Hello! This is a test of the new ElevenLabs Text to Speech integration for AI Vidya."
        print(f"Synthesizing: '{text}'")
        
        result = await tts_service.synthesize_speech(text, gender="FEMALE")
        
        audio_len = len(result["audio_content"])
        print(f"SUCCESS! Received {audio_len} bytes of audio content.")
        
        with open("test_elevenlabs.mp3", "wb") as f:
            f.write(result["audio_content"])
        print("Audio saved to test_elevenlabs.mp3")
        
    except Exception as e:
        print(f"FAILURE: {e}")

if __name__ == "__main__":
    asyncio.run(test_elevenlabs())
