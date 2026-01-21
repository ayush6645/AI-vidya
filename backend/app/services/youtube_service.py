# youtube_service.py - UPDATED
import os
import httpx
import asyncio
import re
import json
from typing import Optional, Dict, Any, List
from urllib.parse import quote_plus
from datetime import datetime, timedelta
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from backend.app.core.config import settings
from backend.app.core import config
from google.cloud import firestore

class EnhancedYouTubeService:
    def __init__(self):
        self.api_key = settings.YOUTUBE_API_KEY
        # db is accessed dynamically from config to ensure it's initialized
        
        # Pre-defined high-quality educational channels
        self.PREFERRED_CHANNELS = {
            'freecodecamp', 'csdojo', 'mitocw', 'stanfordonline', 'harvardonline',
            'thenewboston', 'traversymedia', 'programmingwithmosh', 'coreyms',
            'sentdex', 'fireship', 'webdevsimplified', 'academind', 'techwithtim',
            'edureka', 'simplilearn', 'khanacademy', 'crashcourse', 'thenetninja'
        }
        
        # Keywords that indicate high-quality educational content
        self.QUALITY_KEYWORDS = [
            'tutorial', 'course', 'lecture', 'explained', 'beginners', 'fundamentals',
            'crash course', 'full course', 'complete guide', 'step by step'
        ]
        
        # Keywords to avoid (music, entertainment, etc.)
        self.BLACKLIST_KEYWORDS = [
            'music video', 'song', 'lyrics', 'movie', 'trailer', 'rick astley',
            'rickroll', 'entertainment', 'funny', 'prank', 'memes', 'reaction'
        ]

    async def get_video_for_lesson(self, topic: str, description: str, lesson_id: str) -> Optional[str]:
        """
        Smart YouTube search with quality filtering, caching with expiry, and fallback strategies
        """
        if not self.api_key:
            return self._get_fallback_video()
        
        # Step 1: Check cache with expiry (7 days)
        cached = await self._get_cached_video(lesson_id)
        if cached and not await self._is_cache_expired(cached.get('cached_at')):
            print(f"✅ Using cached video for lesson {lesson_id}")
            return cached.get('embed_url')
        
        # Step 2: Generate optimized search queries
        search_queries = self._generate_search_queries(topic, description)
        
        print(f"\n🔍 Searching YouTube for: {topic}")
        print(f"📝 Generated queries: {search_queries}")
        
        # Step 3: Try each query until we find a good video
        for query in search_queries:
            video_data = await self._search_youtube(query, lesson_id)
            if video_data and self._is_high_quality(video_data):
                # Cache the good video
                await self._cache_video(lesson_id, video_data)
                print(f"✅ Found quality video: {video_data.get('title')}")
                return video_data.get('embed_url')
        
        # Step 4: If no good video found, use fallback but don't cache it
        fallback = self._get_fallback_video()
        print(f"⚠️ Using fallback video for {topic}")
        return fallback
    
    def _generate_search_queries(self, topic: str, description: str) -> List[str]:
        """Generate multiple search query variations"""
        # Clean the topic
        cleaned_topic = re.sub(r'^(Day|Project|Module|Lesson|Week)\s*\d+\s*[:-]\s*', '', topic, flags=re.IGNORECASE)
        cleaned_topic = cleaned_topic.replace('C++', 'C plus plus').replace('c++', 'c plus plus')
        cleaned_topic = cleaned_topic.replace(':', ' ').replace('#', '').strip()
        
        # Extract key terms from description
        if description:
            desc_words = re.findall(r'\b[a-zA-Z]{4,}\b', description.lower())
            key_terms = [word for word in desc_words if word not in 
                        {'this', 'that', 'with', 'from', 'have', 'will', 'your', 'about'}][:3]
        else:
            key_terms = []
        
        queries = []
        
        # Query 1: Main topic + "tutorial for beginners"
        queries.append(f"{cleaned_topic} tutorial for beginners")
        
        # Query 2: Main topic + key terms from description
        if key_terms:
            queries.append(f"{cleaned_topic} {' '.join(key_terms)} tutorial")
        
        # Query 3: Clean topic without extra words
        queries.append(f"learn {cleaned_topic}")
        
        # Query 4: For programming topics
        if any(term in cleaned_topic.lower() for term in ['programming', 'code', 'development', 'software']):
            queries.append(f"{cleaned_topic} programming tutorial")
        
        # Remove duplicates and limit
        unique_queries = []
        seen = set()
        for q in queries:
            if q not in seen and len(q) < 100:  # YouTube has query length limits
                unique_queries.append(q)
                seen.add(q)
        
        return unique_queries[:5]  # Max 5 queries
    
    async def _search_youtube(self, query: str, lesson_id: str) -> Optional[Dict]:
        """Search YouTube with proper encoding and error handling"""
        try:
            encoded_query = quote_plus(query)
            url = (
                f"https://www.googleapis.com/youtube/v3/search"
                f"?part=snippet"
                f"&q={encoded_query}"
                f"&type=video"
                f"&maxResults=10"  # Get more results to choose from
                f"&videoDuration=medium"  # Prefer medium length videos (4-20 min)
                f"&relevanceLanguage=en"
                f"&videoEmbeddable=true"
                f"&key={self.api_key}"
            )
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                items = response.json().get('items', [])
                
                if not items:
                    return None
                
                # Process results
                videos = []
                for item in items:
                    video_id = item['id']['videoId']
                    title = item['snippet']['title'].lower()
                    channel = item['snippet']['channelTitle'].lower()
                    
                    # Get video details for duration
                    detail_url = (
                        f"https://www.googleapis.com/youtube/v3/videos"
                        f"?part=contentDetails,statistics"
                        f"&id={video_id}"
                        f"&key={self.api_key}"
                    )
                    
                    detail_resp = await client.get(detail_url)
                    if detail_resp.status_code == 200:
                        detail = detail_resp.json().get('items', [{}])[0]
                        duration = detail.get('contentDetails', {}).get('duration', 'PT0S')
                        stats = detail.get('statistics', {})
                        
                        # Calculate duration in minutes
                        import isodate
                        try:
                            dur_seconds = isodate.parse_duration(duration).total_seconds()
                            duration_min = dur_seconds / 60
                        except:
                            duration_min = 0
                        
                        video_data = {
                            'video_id': video_id,
                            'title': item['snippet']['title'],
                            'channel': channel,
                            'description': item['snippet'].get('description', ''),
                            'duration_minutes': duration_min,
                            'views': int(stats.get('viewCount', 0)),
                            'likes': int(stats.get('likeCount', 0)),
                            'embed_url': f"https://www.youtube.com/embed/{video_id}",
                            'search_query': query,
                            'searched_at': datetime.utcnow().isoformat()
                        }
                        
                        videos.append(video_data)
                
                # Rank videos by quality
                ranked = sorted(videos, key=lambda v: self._calculate_quality_score(v), reverse=True)
                
                return ranked[0] if ranked else None
                
        except Exception as e:
            print(f"❌ YouTube search error for query '{query}': {e}")
            return None
    
    def _calculate_quality_score(self, video: Dict) -> float:
        """Calculate quality score for a video"""
        score = 0
        
        # Channel quality (50 points)
        if any(channel in video['channel'] for channel in self.PREFERRED_CHANNELS):
            score += 50
        
        # Duration preference (30 points)
        if 5 <= video['duration_minutes'] <= 30:  # Ideal length for lessons
            score += 30
        elif 30 < video['duration_minutes'] <= 60:
            score += 20
        else:
            score += 5
        
        # Title quality (20 points)
        title_lower = video['title'].lower()
        if any(keyword in title_lower for keyword in self.QUALITY_KEYWORDS):
            score += 20
        
        # Engagement (based on likes/views ratio if available)
        if video['views'] > 0 and video['likes'] > 0:
            like_ratio = video['likes'] / video['views']
            if like_ratio > 0.05:  # Good engagement
                score += 30
            elif like_ratio > 0.02:
                score += 15
        
        # Penalize blacklisted content
        title_lower = video['title'].lower()
        if any(blacklisted in title_lower for blacklisted in self.BLACKLIST_KEYWORDS):
            score -= 100
        
        return score
    
    def _is_high_quality(self, video: Dict) -> bool:
        """Check if video meets minimum quality standards"""
        score = self._calculate_quality_score(video)
        
        # Basic quality checks
        title_lower = video['title'].lower()
        
        # Reject blacklisted content
        if any(blacklisted in title_lower for blacklisted in self.BLACKLIST_KEYWORDS):
            return False
        
        # Minimum duration (at least 2 minutes)
        if video['duration_minutes'] < 2:
            return False
        
        # Minimum quality score
        return score >= 30
    
    async def _get_cached_video(self, lesson_id: str) -> Optional[Dict]:
        """Get cached video from Firestore"""
        if not config.db:
            config.init_firebase()
        if not config.db:
            return None
        
        def _get():
            try:
                doc_ref = config.db.collection('youtube_cache').document(lesson_id)
                doc = doc_ref.get()
                return doc.to_dict() if doc.exists else None
            except Exception:
                return None
                
        return await asyncio.to_thread(_get)
    
    async def _cache_video(self, lesson_id: str, video_data: Dict):
        """Cache video data with timestamp"""
        if not config.db:
            config.init_firebase()
        if not config.db:
            return
        
        def _set():
            try:
                cache_data = {
                    **video_data,
                    'cached_at': firestore.SERVER_TIMESTAMP,
                    'lesson_id': lesson_id,
                    'expires_at': datetime.utcnow() + timedelta(days=7)
                }
                
                doc_ref = config.db.collection('youtube_cache').document(lesson_id)
                doc_ref.set(cache_data)
            except Exception as e:
                print(f"⚠️ Failed to cache video: {e}")

        await asyncio.to_thread(_set)
    
    async def _is_cache_expired(self, cached_at) -> bool:
        """Check if cache is expired"""
        if not cached_at:
            return True
        
        if isinstance(cached_at, datetime):
            cache_time = cached_at
        else:
            cache_time = cached_at.replace(tzinfo=None)
        
        return datetime.utcnow() - cache_time > timedelta(days=7)
    
    def _get_fallback_video(self) -> str:
        """Return a relevant educational fallback video (not Rick Astley!)"""
        # Curated list of good educational videos by category
        fallback_videos = {
            'programming': 'https://www.youtube.com/embed/k9WqpQp8VSU',  # CS50 Intro
            'python': 'https://www.youtube.com/embed/rfscVS0vtbw',  # FreeCodeCamp Python
            'web': 'https://www.youtube.com/embed/ysEN5RaKOlA',  # Web Dev in 2024
            'machine learning': 'https://www.youtube.com/embed/i_LwzRVP7bg',  # Andrew Ng ML
            'data science': 'https://www.youtube.com/embed/ua-CiDNNj30',  # Data Science Course
            'default': 'https://www.youtube.com/embed/8mAITcNt710'  # Learning How to Learn
        }
        
        return fallback_videos.get('default')
    
    async def refresh_cache_for_lesson(self, lesson_id: str) -> bool:
        """Force refresh cache for a specific lesson"""
        if not config.db:
            config.init_firebase()
        if not config.db:
            return False

        def _delete():
            try:
                doc_ref = config.db.collection('youtube_cache').document(lesson_id)
                doc_ref.delete()
                print(f"♻️ Cache cleared for lesson {lesson_id}")
                return True
            except Exception:
                return False
        
        return await asyncio.to_thread(_delete)

    async def get_transcript(self, video_url: str) -> Dict[str, Any]:
        """Fetches the transcript for a lesson's YouTube video."""
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

youtube_service = EnhancedYouTubeService()