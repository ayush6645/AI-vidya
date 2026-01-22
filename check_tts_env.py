from google.cloud import texttospeech
import sys

print(f"Python executable: {sys.executable}")
print(f"Library Version: {texttospeech.__version__}")

try:
    print(f"Attempt 1 (Request.TimepointType): {texttospeech.SynthesizeSpeechRequest.TimepointType.SSML_MARK}")
except Exception as e:
    print(f"Attempt 1 failed: {e}")

try:
    # Older versions might have it here?
    print(f"Attempt 2 (SynthesizeSpeechConfig): {texttospeech.SynthesizeSpeechConfig.TimepointType.SSML_MARK}")
except Exception as e:
    print(f"Attempt 2 failed: {e}")

try:
    from google.cloud.texttospeech_v1.types import SynthesizeSpeechRequest
    print(f"Attempt 3 (v1.types.Request): {SynthesizeSpeechRequest.TimepointType.SSML_MARK}")
except Exception as e:
    print(f"Attempt 3 failed: {e}")
