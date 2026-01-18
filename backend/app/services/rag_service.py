import os
import chromadb
from chromadb.utils import embedding_functions
from typing import Dict, Any, List, Optional
from backend.app.core.config import settings
from backend.app.services.llm_service import llm_service
import logging

class RAGService:
    def __init__(self):
        self.chroma_client = None
        self.embedding_fn = None
        self.collection = None
        self.SIMILARITY_THRESHOLD = 0.6

    def _ensure_initialized(self):
        if self.collection: return
        logging.info("Initializing RAG Service (Lazy Loading)...")
        self.chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_DIR)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name="roadmap_rag_context",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )
        logging.info("RAG Service Initialized.")

    def _load_prompt(self, filename: str) -> str:
        try:
            with open(os.path.join(settings.PROMPTS_DIR, filename), 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logging.error(f"Failed to load prompt {filename}: {e}")
            return ""

    def query_context(self, topic: str, level: str, top_k: int = 3) -> Dict[str, Any]:
        """Query ChromaDB for relevant chunks."""
        self._ensure_initialized()
        query_text = f"{topic} {level} roadmap syllabus"
        
        results = self.collection.query(
            query_texts=[query_text],
            n_results=top_k
        )
        
        return results

    async def generate_roadmap_rag(self, topic: str, level: str, duration: int) -> Dict[str, Any]:
        
        # 1. Retrieval
        try:
            results = self.query_context(topic, level, top_k=4)
            distances = results['distances'][0]
            documents = results['documents'][0]
            metadatas = results['metadatas'][0]
        except Exception as e:
            logging.error(f"RAG Retrieval failed: {e}")
            distances = []

        # 2. Eligibility Check
        # Lower distance is better. 
        is_eligible = False
        relevant_chunks = []
        sources = set()

        if distances and distances[0] < self.SIMILARITY_THRESHOLD:
            is_eligible = True
            for i, dist in enumerate(distances):
                if dist < self.SIMILARITY_THRESHOLD:
                    relevant_chunks.append(f"Content: {documents[i]}\nSource: {metadatas[i].get('source_file')}")
                    sources.add(metadatas[i].get('source_file'))
        
        # 3. Prompt Construction & Generation
        if is_eligible:
            generation_mode = "rag"
            template = self._load_prompt("roadmap_rag_v1.txt")
            context_str = "\n---\n".join(relevant_chunks)
            prompt = template.format(
                topic=topic,
                level=level,
                duration=duration,
                context=context_str
            )
            logging.info(f"Generating RAG roadmap for '{topic}' with {len(relevant_chunks)} chunks.")
        else:
            generation_mode = "llm_only"
            template = self._load_prompt("roadmap_llm_v1.txt")
            prompt = template.format(
                topic=topic,
                level=level,
                duration=duration
            )
            logging.info(f"Generating LLM-only roadmap for '{topic}' (No RAG context found).")
            sources = []

        # 4. LLM Call
        roadmap_json = await llm_service.generate_json(prompt)
        
        if not roadmap_json:
             # Fail-safe
             return {
                 "status": "error",
                 "message": "Failed to generate roadmap content"
             }

        # 5. Return Enriched Response
        return {
            "status": "success",
            "generation_mode": generation_mode,
            "sources": list(sources),
            "retrieval_confidence": 1.0 - distances[0] if distances else 0.0,
            "roadmap": roadmap_json
        }

rag_service = RAGService()
