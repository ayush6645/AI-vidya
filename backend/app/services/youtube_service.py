import os
import httpx
import asyncio
from typing import Optional, Dict, Any
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from backend.app.core.config import settings

class YouTubeService:
    def __init__(self):
        self.api_key = settings.YOUTUBE_API_KEY
        
    async def get_video_for_lesson(self, topic: str, description: str) -> Optional[str]:
        if not self.api_key: return None
        
        # dynamic import to avoid circular dependency issues if any arise later
        from backend.app.services.llm_service import llm_service
        
        # 1. Generate Optimized Query using LLM
        search_query = await llm_service.generate_youtube_search_query(topic, description)
        print(f"DEBUG: Optimized YouTube Query: '{search_query}'")
        
        # 2. Fetch Candidates (Increased to 10 for better selection pool)
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": search_query,
            "type": "video",
            "videoEmbeddable": "true",
            "maxResults": 10, 
            "relevanceLanguage": "en",
            "key": self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                items = data.get('items', [])
                
                if items:
                    # Prepare candidates for LLM ranking
                    candidates = []
                    for item in items:
                        candidates.append({
                            'videoId': item['id']['videoId'],
                            'title': item['snippet']['title'],
                            'description': item['snippet']['description'],
                            'channel': item['snippet']['channelTitle']
                        })
                    
                    # 3. LLM Reranking
                    best_video_id = await llm_service.rank_video_candidates(topic, description, candidates)
                    
                    if best_video_id:
                        print(f"DEBUG: LLM selected video: {best_video_id}")
                        return f"https://www.youtube.com/embed/{best_video_id}"
                    
                    # Fallback to first result if LLM returns nothing
                    print("DEBUG: LLM Ranking returned None, using top result.")
                    return f"https://www.youtube.com/embed/{items[0]['id']['videoId']}"
                    
            except Exception as e:
                print(f"YouTube Search Error: {e}")
                
        # Fallback to basic search if optimized failed or returned nothing
        if search_query != f"{topic} tutorial":
             return await self.get_video_for_lesson_basic(topic)
             
        return None

    async def get_video_for_lesson_basic(self, topic: str) -> Optional[str]:
        """Fallback method using simple query"""
        search_query = f"{topic} tutorial"
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": search_query,
            "type": "video",
            "maxResults": 1,
            "key": self.api_key
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    items = resp.json().get('items', [])
                    if items:
                        return f"https://www.youtube.com/embed/{items[0]['id']['videoId']}"
            except Exception:
                pass
        return None

    async def get_transcript(self, video_url: str) -> Dict[str, Any]:
        if 'embed/' not in video_url:
            return {'status': 'error', 'message': 'Invalid URL'}
        
        video_id = video_url.split('embed/')[-1]
        
        def _get_transcript():
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                text = " ".join([t['text'] for t in transcript])
                return {'status': 'success', 'transcript': text}
            except (TranscriptsDisabled, NoTranscriptFound):
                return {'status': 'error', 'message': 'No transcript available'}
            except Exception as e:
                return {'status': 'error', 'message': str(e)}

        return await asyncio.to_thread(_get_transcript)

youtube_service = YouTubeService()
