import logging
import asyncio
from typing import Dict, Any
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

try:
    from elevenlabs.client import ElevenLabs
    ELEVENLABS_AVAILABLE = True
except ImportError as e:
    logger.error(f"CRITICAL: Could not import elevenlabs: {e}")
    ELEVENLABS_AVAILABLE = False
    ElevenLabs = None

class TTSService:
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        if not self.api_key:
            logger.warning("ELEVENLABS_API_KEY not found in settings.")
            self.client = None
        else:
            try:
                self.client = ElevenLabs(api_key=self.api_key)
                logger.info("ElevenLabs Client initialized successfully")
            except Exception as e:
                logger.error("Failed to initialize ElevenLabs Client: %s", e)
                self.client = None

        # Voice IDs for standard ElevenLabs voices
        # NOTE: 'pNInz6obpgDQGcFmaJgB' (Antoni) is confirmed working on this API key.
        # Other IDs like Rachel or Aria might require specific subscription permissions.
        # You can add your own Voice IDs from the ElevenLabs Dashboard here:
        self.voice_mapping = {
            "MALE": "pNInz6obpgDQGcFmaJgB",
            "FEMALE": "pNInz6obpgDQGcFmaJgB", 
            "NEUTRAL": "pNInz6obpgDQGcFmaJgB"
        }

    async def synthesize_speech(self, text: str, gender: str = "NEUTRAL", speed: float = 1.0) -> Dict[str, Any]:
        if not ELEVENLABS_AVAILABLE:
            logger.error("ElevenLabs SDK is not installed.")
            raise Exception("TTS Service unavailable: ElevenLabs SDK missing.")

        if not self.client:
            logger.error("ElevenLabs Client not initialized (missing API key?)")
            raise Exception("TTS Client not initialized. Please check ELEVENLABS_API_KEY.")

        voice_id = self.voice_mapping.get(gender.upper(), "pNInz6obpgDQGcFmaJgB")
        
        logger.info(f"Synthesizing speech with ElevenLabs (Voice ID: {voice_id}, Speed: {speed})")

        def _call_elevenlabs():
            try:
                audio_generator = self.client.text_to_speech.convert(
                    voice_id=voice_id,
                    text=text,
                    model_id="eleven_multilingual_v2"
                )
                
                # Collect the generator output into a single bytes object
                return b"".join(audio_generator)
            except Exception as e:
                logger.error(f"ElevenLabs Synthesis Error: {e}")
                raise e

        try:
            audio_content = await asyncio.to_thread(_call_elevenlabs)
            return {
                "audio_content": audio_content,
                "text": text,
                "provider": "elevenlabs"
            }
        except Exception as e:
            logger.error(f"TTS Synthesis Failed: {str(e)}")
            raise Exception(f"Failed to synthesize speech: {str(e)}")

tts_service = TTSService()
