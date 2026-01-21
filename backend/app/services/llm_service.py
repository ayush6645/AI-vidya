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
        self.groq_key = settings.GROQ_API_KEY
        
        if not self.api_key:
            print("Warning: GOOGLE_API_KEY is not set.")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)

        if self.groq_key:
            from groq import Groq
            self.groq_client = Groq(api_key=self.groq_key)
            # Use Llama model for regular text generation tasks
            self.groq_model_id = 'llama-3.3-70b-versatile'
        else:
            self.groq_client = None
            print("Warning: GROQ_API_KEY is not set.")

        # Default fallback
        self.model_id = 'gemini-2.0-flash'

    async def generate_json(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Generic method to generate JSON from a prompt using Groq (Primary) or Gemini (Fallback)."""
        
        # 1. Try Groq (Preferred for unlimited Llama 3.3 usage)
        if self.groq_client:
            def _call_groq():
                try:
                    response = self.groq_client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model=self.groq_model_id,
                        response_format={"type": "json_object"} # Native JSON mode
                    )
                    return json.loads(response.choices[0].message.content)
                except Exception as e:
                    print(f"Groq API Error: {e}. Falling back to Gemini...")
                    return None
            
            result = await asyncio.to_thread(_call_groq)
            if result: return result

        # 2. Fallback to Gemini
        if not self.client: return None
        
        def _call_gemini():
            try:
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=[{"role": "user", "parts": [{"text": prompt}]}]
                )
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

    async def generate_plan(self, topic: str, difficulty: str, timeline: str, time_investment: str = "2 hours/day") -> Optional[Dict[str, Any]]:
        """
        Generates a detailed, day-by-day learning plan using a high-quality prompt.
        Designed to create structured, academic-quality curriculum without RAG dependency.
        """
        # Calculate total days based on timeline
        if isinstance(timeline, int):
             timeline_days = timeline * 30
        elif str(timeline).isdigit():
             timeline_days = int(timeline) * 30
        else:
            timeline_days = {
                '1_month': 30,
                '2_months': 60,
                '3_months': 90,
                '6_months': 180
            }.get(str(timeline), 30)
            
        # Ensure minimum days per module
        min_days_per_module = max(3, timeline_days // 10)  # At least 3 days per module
        
        prompt = f"""
        Create a detailed learning plan for: {topic}
        Difficulty: {difficulty}
        Total Duration: {timeline} ({timeline_days} days)
        Daily Time Investment: {time_investment}
        
        IMPORTANT RULES:
        1. Create EXACTLY {timeline_days} days of content (MANDATORY)
        2. Divide into logical modules (approx {max(1, timeline_days // 10)} modules)
        3. Each module should have {min_days_per_module}-15 days
        4. Each day should have a specific, actionable topic
        5. Include project days and review days
        6. Ensure the progression builds logically
        
        Format as JSON with strictly this structure:
        {{
          "plan_title": "Title",
          "difficulty_level": "{difficulty}",
          "total_duration_months": "{timeline}",
          "modules": [
            {{
              "module_number": 1,
              "module_title": "Title",
              "lessons": [
                {{
                  "day_of_plan": 1,
                  "topic": "Topic",
                  "description": "Description",
                  "Youtube_keywords": "educational search terms"
                }}
              ]
            }}
          ]
        }}
        
        Ensure day_of_plan counts strictly from 1 to {timeline_days}.
        """
        return await self.generate_json(prompt)

    async def generate_summary_and_quiz(self, title: str, description: str) -> Dict[str, Any]:
        """
        Generates a concise summary and a 3-question quiz for a given lesson.
        Uses a robust prompt to ensure valid JSON output.
        """
        if not self.client: 
            return {"summary": "Service unavailable", "quiz": []}

        prompt = f"""
        Role: Educational Content Creator
        Task: Create a learning summary and a short quiz for the following lesson.

        Lesson Topic: {title}
        Context: {description}

        Requirements:
        1. **Summary**: Write a clear, engaging, and educational summary (3-4 paragraphs). Explain the key concepts simply.
        2. **Quiz**: Create exactly 3 multiple-choice questions based on the summary.
           - 'options': Provide 4 choices.
           - 'answer': Must be one of the options (exact Text match).

        Output Format:
        - STRICTLY valid JSON.
        - NO markdown code blocks (e.g. ```json).
        - Use this schema:

        {{
            "summary": "Full summary text here...", 
            "quiz": [
                {{
                    "question": "Question text?", 
                    "options": ["Option A", "Option B", "Option C", "Option D"], 
                    "answer": "Option A"
                }},
                ... (2 more questions)
            ]
        }}
        """
        result = await self.generate_json(prompt)
        if not result:
             return {"summary": "Content generation failed. Please try again.", "quiz": []}
        return result

    async def generate_youtube_search_query(self, topic: str, description: str) -> str:
        """Generates an optimized YouTube search query using Groq (Primary) or Gemini."""
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
        
        # 1. Try Groq
        if self.groq_client:
            def _call_groq_text():
                try:
                    response = self.groq_client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model=self.groq_model_id,
                    )
                    return response.choices[0].message.content.strip().replace('"', '')
                except Exception as e:
                    print(f"Groq Query Gen Error: {e}")
                    return None
            
            res = await asyncio.to_thread(_call_groq_text)
            if res: return res

        # 2. Fallback Gemini
        if not self.client: return f"{topic} tutorial"

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
                
        return await asyncio.to_thread(_call_gemini_text)

    async def rank_video_candidates(self, topic: str, description: str, candidates: list) -> Optional[str]:
        """
        Uses LLM (Groq Preferred) to analyze video metadata and pick the best educational match.
        candidates: List of dicts { 'videoId': str, 'title': str, 'description': str, 'channel': str }
        """
        if not candidates: return None

        candidates_str = json.dumps(candidates, indent=2)
        
        prompt = f"""
        You are an AI Learning Architect and Content Quality Controller.
        
        Task: Select the BEST YouTube video for this lesson from the candidates below.
        
        Lesson Topic: {topic}
        Lesson Description: {description}

        Candidate Videos:
        {candidates_str}

        ═══════════════════════════════════════════════════════════
        STRICT VIDEO SELECTION RULES (NON-NEGOTIABLE)
        ═══════════════════════════════════════════════════════════
        
        HARD REJECTIONS (IMMEDIATE DISQUALIFICATION):
        Reject ANY video if title/description contains:
        ❌ "Official Video", "MusicVideo", "MV", "lyrics"
        ❌ "song", "remix", "cover", "live performance", "concert"
        ❌ YouTube Short (< 1 min)
        ❌ Under 8 minutes duration
        ❌ "reaction", "funny", "comedy", "prank", "challenge"
        ❌ Entertainment, pop culture, celebrity content
        ❌ "top 10", "best of", listicles (unless purely educational)
        ❌ Clickbait or trend-based content
        ❌ NOT primarily instructional
        
        TITLE/DESCRIPTION MUST CONTAIN (At least ONE):
        ✅ "tutorial", "explained", "lecture", "course", "lesson"
        ✅ "step by step", "guide", "introduction", "learn", "how to"
        ✅ "crash course", "training", "workshop", "masterclass"
        ❌ Has vague titles without educational intent
        
        ═══════════════════════════════════════════════════════════
        VIDEO INCLUSION RULES (REQUIRED)
        ═══════════════════════════════════════════════════════════
        
        Accept ONLY videos that:
        ✅ Clearly explain the exact lesson topic
        ✅ Include examples, demonstrations, or walkthroughs
        ✅ Use educational intent terms:
           - "tutorial", "explained", "lecture", "full course"
           - "step by step", "guide", "introduction", "deep dive"
        ✅ PRIMARY purpose is to TEACH (not entertain)
        
        ═══════════════════════════════════════════════════════════
        SEMANTIC VALIDATION (CRITICAL - MUST PASS)
        ═══════════════════════════════════════════════════════════
        
        Before accepting ANY video, ask yourself:
        "Is the PRIMARY purpose of this video to TEACH {topic}?"
        
        If NOT a clear YES → REJECT IMMEDIATELY
        
        Validation Steps:
        1. Title + Description STRONGLY align with lesson topic?
        2. PRIMARY purpose is to TEACH this specific concept?
        3. No partial matches or tangential content?
        4. Not just mentioning topic, but INSTRUCTING on it?
        
        If ANY validation fails → REJECT the video
        
        ═══════════════════════════════════════════════════════════
        QUALITY HIERARCHY
        ═══════════════════════════════════════════════════════════
        
        Tier 1 (BEST):
        - Established educators: "CrashCourse", "FreeCodeCamp", "Traversy Media"
        - Academic channels: "MIT OpenCourseWare", "Stanford", "Khan Academy"
        - Expert creators: "3Blue1Brown", "Veritasium", "Fireship"
        
        Tier 2 (GOOD):
        - Professional tutorials matching exact topic
        - Clear teaching structure
        - Good production quality
        
        Tier 3 (ACCEPTABLE):
        - Accurate content but lower production value
        - Must still match ALL inclusion rules
        
        ═══════════════════════════════════════════════════════════
        OUTPUT INSTRUCTIONS
        ═══════════════════════════════════════════════════════════
        
        Return ONLY the 'videoId' of the best match.
        
        If NO video meets the standards:
        - Return EXACTLY: "None"
        
        If multiple videos qualify:
        - Select the highest quality (Tier 1 > Tier 2 > Tier 3)
        - Prefer longer, comprehensive tutorials
        - Prefer newer content (if quality is equal)
        
        ═══════════════════════════════════════════════════════════
        REMEMBER
        ═══════════════════════════════════════════════════════════
        
        User wants to STUDY seriously, not browse.
        Prioritize ACCURACY and EDUCATIONAL VALUE.
        When in doubt → REJECT.
        """
        
        # 1. Try Groq
        if self.groq_client:
            def _call_groq_rank():
                try:
                    response = self.groq_client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model=self.groq_model_id,
                    )
                    result = response.choices[0].message.content.strip().replace('"', '').replace("'", "")
                    if len(result) > 20 or "None" in result: return None
                    return result
                except Exception as e:
                    print(f"Groq Ranking Error: {e}")
                    return None
            
            res = await asyncio.to_thread(_call_groq_rank)
            if res: return res

        # 2. Fallback Gemini
        if not self.client: return None
        
        def _call_gemini_rank():
            try:
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=[{"role": "user", "parts": [{"text": prompt}]}]
                )
                result = response.text.strip().replace('"', '').replace("'", "")
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
