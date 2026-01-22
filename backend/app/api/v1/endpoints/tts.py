from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
from backend.app.services.tts_service import tts_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class TTSRequest(BaseModel):
    text: str
    gender: str = "NEUTRAL"
    speed: float = 1.0

import base64

@router.get("/simple-test")
async def test_tts_simple():
    """Simple GET endpoint for testing TTS"""
    try:
        # Hardcoded test
        result = await tts_service.synthesize_speech(text="This is a simple audio test.")
        
        return Response(
            content=result["audio_content"], 
            media_type="audio/mpeg"
        )
    except Exception as e:
        logger.error(f"Simple TTS test failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/speak")
async def speak_text(request: TTSRequest):
    """
    Convert text to speech and return audio file directly.
    """
    try:
        logger.info(f"Received TTS request: {len(request.text)} chars")
        
        # Validate input
        if not request.text or len(request.text.strip()) == 0:
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        if len(request.text) > 10000:
            raise HTTPException(status_code=400, detail="Text too long (max 10000 chars)")
        
        # Synthesize speech
        result = await tts_service.synthesize_speech(
            text=request.text,
            gender=request.gender,
            speed=request.speed
        )
        
        # Return raw audio content
        return Response(
            content=result["audio_content"],
            media_type="audio/mpeg"
        )
        
    except Exception as e:
        logger.error(f"TTS endpoint error: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e), "message": "TTS Service Error"}
        )

@router.get("/health")
async def tts_health():
    """Check TTS service health"""
    try:
        if tts_service.client:
            return {
                "status": "healthy",
                "service": "google_text_to_speech",
                "available": True
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "service": "google_text_to_speech",
                    "available": False,
                    "error": "TTS client not initialized"
                }
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e)}
        )
