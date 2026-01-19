try:
    from youtube_transcript_api import YouTubeTranscriptApi
    print(f"Type: {type(YouTubeTranscriptApi)}")
    print(f"Dir: {dir(YouTubeTranscriptApi)}")
    
    # Try instantiation just in case
    # t = YouTubeTranscriptApi()
    # print("Instantiated")
except Exception as e:
    print(f"Error: {e}")
