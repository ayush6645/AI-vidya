import asyncio
import os
import tempfile
import yt_dlp
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ytdlp_download(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    with tempfile.TemporaryDirectory() as temp_dir:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(temp_dir, '%(id)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'nocheckcertificate': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'referer': 'https://www.google.com/',
            'headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Sec-Fetch-Mode': 'navigate',
            }
        }
        
        try:
            logger.info(f"Testing download for {video_id}...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                await asyncio.to_thread(ydl.download, [url])
            
            files = os.listdir(temp_dir)
            print(f"Files in temp dir: {files}")
            if files:
                print("SUCCESS: Audio downloaded!")
            else:
                print("FAILURE: No files found.")
                
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    # Test with the video ID that failed earlier
    asyncio.run(test_ytdlp_download("FaFT8uotDus"))
