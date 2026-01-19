# Fix for Azure: Replace system sqlite3 with pysqlite3-binary
import sys
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass  # pysqlite3 not available, use system sqlite3

import os
import asyncio
import json
import logging
import tempfile
import yt_dlp
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from youtube_transcript_api import YouTubeTranscriptApi
from typing import List, Dict, Any, Optional

from backend.app.services.llm_service import llm_service
from backend.app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

class GeminiEmbeddingFunction(chromadb.EmbeddingFunction):
    """
    Custom ChromaDB Embedding Function using Gemini API via LLMService.
    """
    def __call__(self, input: chromadb.Documents) -> chromadb.Embeddings:
        # LLMService returns a list of lists of floats
        # Synchronization wrapper since Chroma expects sync call here, 
        # but llm_service is async. We might need to run it in a loop.
        # However, calling async from sync is tricky.
        # HACK: Using a new event loop or run_until_complete if not in loop.
        
        # Better approach: Pre-calculate embeddings before adding to Chroma?
        # Or just use `requests` (sync) inside here to call Gemini directly?
        # Re-using LLMService async method inside sync callback is hard.
        
        # ACTUALLY: Let's separate embedding generation from Chroma add.
        # We will generate embeddings first, then pass them to collection.add(embeddings=...)
        # So we don't strictly need this class if we handle it manually.
        pass

class VideoRAGService:
    def __init__(self):
        # ChromaDB Lazy Init
        self.chroma_client = None
        self.collection = None
        self.collection_name = "video_transcripts"
        self.chroma_dir = settings.CHROMA_DB_DIR

    def _ensure_initialized(self):
        if self.collection: return
        
        logging.info("Initializing Video RAG Service (Lazy Loading)...")
        try:
             # Ensure SQLite hack (if rag_service didn't run yet)
            try:
                __import__('pysqlite3')
                sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
            except ImportError:
                pass

            os.makedirs(self.chroma_dir, exist_ok=True)
            self.chroma_client = chromadb.PersistentClient(path=self.chroma_dir)
            self.collection = self.chroma_client.get_or_create_collection(name=self.collection_name)
            logging.info("Video RAG Service Initialized.")
        except Exception as e:
            logging.error(f"Video RAG Init Failed: {e}")

    async def get_or_create_interaction_session(self, video_id: str):
        self._ensure_initialized()
        """
        Ensures the video is indexed and ready for chat.
        """
        """
        Ensures the video is indexed and ready for chat.
        """
        # Phase 4 Check: Is video already indexed?
        # We query the collection for metadata video_id match (limit 1)
        # Chroma filtering
        existing = self.collection.get(
            where={"video_id": video_id},
            limit=1
        )
        
        if existing['ids']:
            logger.info(f"Video {video_id} found in vector store. Using cached embeddings.")
            return True
        
        logger.info(f"Video {video_id} not indexed. Starting indexing pipeline.")
        return await self._index_video(video_id)

    async def _index_video(self, video_id: str):
        # Phase 1: Transcript
        transcript_text = await self._fetch_transcript(video_id)
        if not transcript_text:
            logger.error(f"Failed to fetch transcript for {video_id}")
            return False
            
        # Phase 3: Chunking
        chunks = self._chunk_text(transcript_text, chunk_size=1000, overlap=100)
        
        # Generate Embeddings (Phase 4)
        # Batching might be needed if transcript is huge.
        embeddings = await llm_service.get_embeddings(chunks)
        
        if not embeddings:
            logger.error(f"Failed to generate embeddings for {video_id}")
            return False
            
        # Add to Chroma
        ids = [f"{video_id}_{i}" for i in range(len(chunks))]
        metadatas = [{"video_id": video_id, "chunk_index": i, "source": "transcript"} for i in range(len(chunks))]
        
        self.collection.add(
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Successfully indexed video {video_id} with {len(chunks)} chunks.")
        return True

    async def _fetch_transcript(self, video_id: str) -> Optional[str]:
        # Try youtube-transcript-api first
        try:
            # Method 1: list_transcripts (More robust)
            transcript_list = await asyncio.to_thread(YouTubeTranscriptApi.list_transcripts, video_id)
            # Try finding English or auto-generated
            try:
                transcript = transcript_list.find_transcript(['en'])
            except:
                try:
                    transcript = transcript_list.find_generated_transcript(['en'])
                except:
                    # Fallback to any available
                    transcript = transcript_list[0]
            
            fetched_transcript = await asyncio.to_thread(transcript.fetch)
            full_text = " ".join([t['text'] for t in fetched_transcript])
            logger.info(f"Details: Transcript fetched via list_transcripts for {video_id}")
            return full_text
            
        except Exception as e:
            logger.warning(f"list_transcripts failed: {e}. Trying get_transcript.")
            try:
                # Method 2: Old static method
                transcript_list = await asyncio.to_thread(YouTubeTranscriptApi.get_transcript, video_id)
                full_text = " ".join([t['text'] for t in transcript_list])
                return full_text
            except Exception as e2:
                logger.warning(f"Transcript API failed for {video_id}: {e2}. Trying audio fallback.")
            
        # Fallback: Audio Download + Gemini Transcribe (Phase 2)
        return await self._fallback_audio_transcription(video_id)

    async def _fallback_audio_transcription(self, video_id: str) -> Optional[str]:
        # Using yt-dlp to download audio
        # Using tempfile to avoid permanent storage
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Removed FFmpeg dependency. Just download best audio (usually m4a or webm).
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(temp_dir, '%(id)s.%(ext)s'),
                'quiet': True
            }
            
            try:
                logger.info(f"Downloading audio for {video_id}...")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    await asyncio.to_thread(ydl.download, [url])
                
                # Find the file (could be m4a, webm, etc.)
                files = os.listdir(temp_dir)
                audio_file = None
                for f in files:
                    if f.endswith(('.mp3', '.m4a', '.webm', '.wav', '.aac')):
                        audio_file = os.path.join(temp_dir, f)
                        break
                
                if not audio_file:
                    logger.error("Audio download finished but file missing or unknown extension.")
                    return None
                    
                # Transcribe with Gemini (Phase 2)
                # Need LLMService to support file upload or send bytes?
                # Gemini 1.5 Flash supports audio.
                # However, Google GenAI SDK 'generate_content' usually takes PIL images or text.
                # For Audio, we typically use the File API.
                # Let's try to upload it.
                
                logger.info("Transcribing audio with Gemini...")
                # HACK: Using standard genai client from llm_service
                if not llm_service.client:
                    return None
                    
                # We need to use the 'media' upload feature or pass bytes if small?
                # The SDK has 'types.Part.from_data' or we can upload file.
                
                # To keep it simple and within the current context, 
                # let's assume valid API key allows file upload.
                
                # Since 'genai.Client' is used in llm_service, let's access the underlying upload capability if possible.
                # The V2 SDK (google-genai) or V1 (google-generativeai)? 
                # requirements.txt has `google-genai`. This is the new V1 Beta or V2 SDK.
                # Actually `google-genai` package name usually refers to the older or specifically the new SDK.
                # If it is `google-generativeai`, we do `genai.upload_file`.
                # If it is `google-genai` (new), it has distinct client.
                # Let's verify what `genai` is in `llm_service.py`: `from google import genai` indicates the NEW SDK.
                
                # New SDK Usage:
                # client.files.upload(path=...)
                
                # Upload
                # The google-genai SDK uses 'file' parameter, not 'path'
                upload_file = await asyncio.to_thread(llm_service.client.files.upload, file=audio_file)
                
                # Wait for file to be ready
                # Using a loop to check state, as processing can take a few seconds
                import time
                while True:
                    file_check = await asyncio.to_thread(llm_service.client.files.get, name=upload_file.name)
                    if file_check.state.name == "ACTIVE":
                        break
                    elif file_check.state.name == "FAILED":
                        raise Exception("Gemini File Processing Failed")
                    
                    logger.info("Waiting for audio file to process...")
                    await asyncio.sleep(2)
                
                logger.info(f"File ready for processing: {upload_file.name}. Starting generation with gemini-2.0-flash...")
                
                try:
                    response = await asyncio.to_thread(
                        llm_service.client.models.generate_content,
                        model='gemini-2.0-flash',
                        contents=[
                            upload_file,
                            "Generate a full verbatim transcript of this audio."
                        ]
                    )
                    return response.text
                except Exception as e_gen:
                    logger.error(f"Gemini 2.0 generation failed: {e_gen}. Retrying with 1.5-flash...")
                    try:
                        response = await asyncio.to_thread(
                            llm_service.client.models.generate_content,
                            model='gemini-1.5-flash',
                            contents=[
                                upload_file,
                                "Generate a full verbatim transcript of this audio."
                            ]
                        )
                        return response.text
                    except Exception as e_gen_2:
                        logger.error(f"Gemini 1.5 generation also failed: {e_gen_2}")
                        return None

            except Exception as e:
                logger.error(f"Fallback transcription failed: {e}")
                return None

    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        # Simple overlap chunking
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunks.append(text[start:end])
            start += (chunk_size - overlap)
        
        return chunks

    async def chat(self, video_id: str, question: str) -> Dict[str, Any]:
        # Ensure indexed
        is_ready = await self.get_or_create_interaction_session(video_id)
        if not is_ready:
            return {"answer": "I couldn't process this video. It might be private or unavailable.", "source": "system"}
            
        # Retrieval (Phase 5)
        # Embed question
        q_embed = await llm_service.get_embeddings([question])
        if not q_embed:
             return {"answer": "Error processing your question.", "source": "system"}
             
        results = self.collection.query(
            query_embeddings=q_embed,
            n_results=5,
            where={"video_id": video_id}
        )
        
        # Context Assembly
        context_list = results['documents'][0]
        context_str = "\n\n".join(context_list)
        
        # Generation
        prompt = f"""
        You are an AI assistant answering questions about a specific video based STRICTLY on the transcript chunks provided below.
        
        CONTEXT:
        {context_str}
        
        QUESTION:
        {question}
        
        INSTRUCTIONS:
        1. Answer the question using ONLY the provided context.
        2. If the answer is not in the context, say "I don't see that information in the video."
        3. Be concise and direct.
        """
        
        response = await llm_service.generate_json(prompt) # Using generate_json wrapper? No, it expects JSON. 
        # llm_service.generate_json forces JSON. We want text chat.
        # We need a plain text generation method in llm_service, or reuse _call_gemini logic.
        # Let's just use `client.models.generate_content` directly if possible or add `generate_text` to llm_service.
        
        # HACK: I'll use `llm_service.client` directly here for text generation as `generate_json` is strict.
        
        try:
            resp = await asyncio.to_thread(
                llm_service.client.models.generate_content,
                model='gemini-2.0-flash',
                contents=prompt
            )
            return {"answer": resp.text, "source": "video_rag", "context_chunks": len(context_list)}
        except Exception as e:
            return {"answer": "I encountered an error generating the answer.", "source": "system_error"}

video_rag_service = VideoRAGService()
