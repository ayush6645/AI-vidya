
import sys
import os

with open("debug_output.txt", "w") as f:
    f.write(f"Python Executable: {sys.executable}\n")
    f.write(f"Python Path: {sys.path}\n")

    try:
        import youtube_transcript_api
        f.write(f"Module youtube_transcript_api: {youtube_transcript_api}\n")
        f.write(f"File: {youtube_transcript_api.__file__}\n")
        
        from youtube_transcript_api import YouTubeTranscriptApi
        f.write(f"Type of YouTubeTranscriptApi: {type(YouTubeTranscriptApi)}\n")
        f.write(f"Dir: {dir(YouTubeTranscriptApi)}\n")
        
        if hasattr(YouTubeTranscriptApi, 'list_transcripts'):
            f.write("list_transcripts exists.\n")
        else:
            f.write("list_transcripts MISSING.\n")
            
        if hasattr(YouTubeTranscriptApi, 'get_transcript'):
            f.write("get_transcript exists.\n")
        else:
            f.write("get_transcript MISSING.\n")

    except ImportError as e:
        f.write(f"ImportError: {e}\n")

