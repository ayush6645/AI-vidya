import os
import re
import json
import asyncio
from typing import Dict, Any, Optional
from google import genai
from backend.app.core.config import settings

class LLMService:
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        if not self.api_key:
            print("Warning: GOOGLE_API_KEY is not set.")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)
        self.model_id = 'gemini-2.5-flash'

    async def generate_json(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Generic method to generate JSON from a prompt."""
        if not self.client: return None
        
        def _call_gemini():
            try:
                # Add instructions for JSON if not present? 
                # Better to assume prompt handles it or we enforce it here.
                # But for now, just raw call.
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=[{"role": "user", "parts": [{"text": prompt}]}]
                )
                # Clean markdown code blocks if present
                text = response.text
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0]
                elif "```" in text:
                    text = text.split("```")[1]
                
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
                return None
            except Exception as e:
                print(f"Gemini JSON Error: {e}")
                return None

        return await asyncio.to_thread(_call_gemini)

    async def generate_plan(self, topic: str, difficulty: str, timeline_months: int) -> Optional[Dict[str, Any]]:
        """Legacy method for Plan Generation (Phase 1)"""
        # Re-using the prompt logic but could route via generate_json
        prompt = f"""
        Generate a day-by-day learning plan for:
        Topic: "{topic}" | Level: "{difficulty}" | Duration: {timeline_months} months

        Constraints:
        1. Total lessons = {int(timeline_months) * 20} (20 days/month).
        2. Pace: Basic -> Advanced. No filler days.
        3. Output JSON ONLY. No markdown.

        Expected JSON Structure:
        {{
          "plan_title": "string",
          "modules": [
            {{
              "module_title": "string",
              "module_number": 1,
              "lessons": [
                {{
                  "day_of_plan": 1,
                  "topic": "string",
                  "description": "string",
                  "Youtube_keywords": "string"
                }}
              ]
            }}
          ]
        }}
        """
        return await self.generate_json(prompt)

    async def generate_summary_and_quiz(self, title: str, description: str) -> Dict[str, Any]:
        """Legacy method for Summary/Quiz (Phase 1)"""
        if not self.client: 
            return {"summary": "Service unavailable", "quiz": []}

        prompt = f"""
        Lesson Topic: {title}
        Lesson Description: {description}

        Task 1: Summary (4-5 paragraphs, educational).
        Task 2: Quiz (3 questions, multiple choice).

        JSON Output Format:
        {{
            "summary": "string", 
            "quiz": [
                {{"question": "string", "options": ["string"], "answer": "string"}}
            ]
        }}
        """
        result = await self.generate_json(prompt)
        if not result:
             return {"summary": "Generation failed", "quiz": []}
        return result

    async def generate_youtube_search_query(self, topic: str, description: str) -> str:
        """Generates an optimized YouTube search query."""
        if not self.client: return f"{topic} tutorial"
        
        prompt = f"""
        Role: YouTube Search Expert
        Task: Create ONE optimized search query to find the best educational video for this lesson.
        
        Lesson Info:
        - Topic: {topic}
        - Description: {description}
        
        Rules:
        1. Query should be specific but not too long (max 10 words).
        2. Prioritize "tutorial", "course", "explained", or "guide".
        3. Remove filler words.
        4. Output ONLY the search query string. No quotes.
        """
        
        def _call_gemini_text():
            try:
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=[{"role": "user", "parts": [{"text": prompt}]}]
                )
                return response.text.strip().replace('"', '')
            except Exception as e:
                print(f"Gemini Query Gen Error: {e}")
                return f"{topic} tutorial"

    async def rank_video_candidates(self, topic: str, description: str, candidates: list) -> Optional[str]:
        """
        Uses LLM to analyze video metadata and pick the best educational match.
        candidates: List of dicts { 'videoId': str, 'title': str, 'description': str, 'channel': str }
        """
        if not self.client or not candidates: return None

        candidates_str = json.dumps(candidates, indent=2)
        
        prompt = f"""
        Role: Senior Curriculum Curator
        Task: Select the best YouTube video for the following lesson.

        Lesson Topic: {topic}
        Lesson Description: {description}

        Candidate Videos:
        {candidates_str}

        Criteria:
        1. RELEVANCE: Content must strictly match the lesson topic.
        2. QUALITY: Prefer "CrashCourse", "FreeCodeCamp", "Traversy Media", "Veritasium", "3Blue1Brown" or known educators if present.
        3. AVOID: Clickbait, very short clips (<2 mins), or irrelevant gaming/vlog content.
        4. SPECIFICITY: If the lesson is about specific syntax, prefer coding tutorials. If conceptual, prefer visual explainers.

        Output:
        Return ONLY the 'videoId' of the best single match. If none are good, return "None".
        """
        
        def _call_gemini_rank():
            try:
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=[{"role": "user", "parts": [{"text": prompt}]}]
                )
                result = response.text.strip().replace('"', '').replace("'", "")
                # Simple validation to ensure it looks like a video ID (usually 11 chars)
                if len(result) > 20 or "None" in result: 
                    return None
                return result
            except Exception as e:
                print(f"Gemini Ranking Error: {e}")
                return None

        return await asyncio.to_thread(_call_gemini_rank)

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        if not self.client: return []
        
        def _embed():
            try:
                # Use gemini-embedding-1.0 as per user availability
                response = self.client.models.embed_content(
                    model='gemini-embedding-1.0',
                    contents=texts
                )
                # response.embeddings might be list of ContentEmbedding objects
                # Need to extract 'values'
                return [e.values for e in response.embeddings]
            except Exception as e:
                print(f"Gemini Embedding Error: {e}")
                return []

        return await asyncio.to_thread(_embed)

llm_service = LLMService()
