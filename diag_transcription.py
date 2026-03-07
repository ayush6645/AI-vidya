import youtube_transcript_api
from youtube_transcript_api import YouTubeTranscriptApi
import inspect

print("--- Module Level ---")
print(dir(youtube_transcript_api))

print("--- Class Level ---")
print(dir(YouTubeTranscriptApi))

v_id = 'dQw4w9WgXcQ'
print(f"\n--- Testing for video {v_id} ---")

try:
    print("Trying YouTubeTranscriptApi.get_transcript...")
    transcript = YouTubeTranscriptApi.get_transcript(v_id)
    print("SUCCESS: get_transcript works!")
except Exception as e:
    print(f"FAILED: get_transcript: {e}")

try:
    print("\nTrying YouTubeTranscriptApi().list(v_id)...")
    api = YouTubeTranscriptApi()
    transcript_list = api.list(v_id)
    print("SUCCESS: api.list works!")
except Exception as e:
    print(f"FAILED: api.list: {e}")

try:
    print("\nTrying YouTubeTranscriptApi.list_transcripts...")
    tl = YouTubeTranscriptApi.list_transcripts(v_id)
    print("SUCCESS: list_transcripts works!")
except Exception as e:
    print(f"FAILED: list_transcripts: {e}")
