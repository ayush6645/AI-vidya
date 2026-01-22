import logging
import os
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

# Safe Import for Cloud Run environment where dependencies might conflict
try:
    from google.cloud import texttospeech
    TTS_AVAILABLE = True
except ImportError as e:
    logger.error(f"CRITICAL: Could not import google.cloud.texttospeech: {e}")
    TTS_AVAILABLE = False
    texttospeech = None  # Define simple fallback or None

class TTSService:
    def __init__(self):
        # Log credential information
        creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'Not set')
        logger.info(f"TTS Service Initializing... Credentials path: {creds_path}")
        
        try:
            # Check if credentials file exists
            if creds_path and os.path.exists(creds_path):
                logger.info(f"Credentials file exists: {creds_path}")
                # Explicitly load credentials
                self.client = texttospeech.TextToSpeechClient(credentials=service_account.Credentials.from_service_account_file(creds_path))
            else:
                logger.warning("GOOGLE_APPLICATION_CREDENTIALS not found or invalid. Trying default auth.")
                self.client = texttospeech.TextToSpeechClient()
            
            logger.info("✅ TTS Client initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize TTS Client: {e}")
            self.client = None

    async def synthesize_speech(self, text: str, gender: str = "NEUTRAL", speed: float = 1.0):
        if not TTS_AVAILABLE:
            logger.error("TTS Service is unavailable due to import error.")
            raise Exception("TTS Service unavailable on this server instance.")

        if not self.client:
            raise Exception("TTS Client not initialized")
        
        # 1. Simple text input (no SSML, no marks)
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # 2. Voice selection (basic)
        ssml_gender = texttospeech.SsmlVoiceGender.NEUTRAL
        if gender.upper() == "MALE":
            ssml_gender = texttospeech.SsmlVoiceGender.MALE
        elif gender.upper() == "FEMALE":
            ssml_gender = texttospeech.SsmlVoiceGender.FEMALE
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            ssml_gender=ssml_gender
        )
        
        # 3. Audio config
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speed
        )
        
        # 4. SIMPLE API CALL (no timepoints)
        response = self.client.synthesize_speech(
            input=synthesis_input, 
            voice=voice, 
            audio_config=audio_config
        )
        
        return {
            "audio_content": response.audio_content,
            "text": text
        }

tts_service = TTSService()
