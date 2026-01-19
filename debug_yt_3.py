import sys
try:
    import youtube_transcript_api
    print(f"Package: {youtube_transcript_api}")
    print(f"Package File: {getattr(youtube_transcript_api, '__file__', 'No file')}")
    
    from youtube_transcript_api import YouTubeTranscriptApi
    print(f"Class: {YouTubeTranscriptApi}")
    print(f"Class Dict: {YouTubeTranscriptApi.__dict__.keys()}")
except Exception as e:
    print(f"Error: {e}")
