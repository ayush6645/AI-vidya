try:
    from youtube_transcript_api import YouTubeTranscriptApi
    print(f"Library file: {YouTubeTranscriptApi.__file__}")
    print(f"Has get_transcript: {hasattr(YouTubeTranscriptApi, 'get_transcript')}")
    # Inspect dir
    print(dir(YouTubeTranscriptApi))
except Exception as e:
    print(f"Import Error: {e}")
