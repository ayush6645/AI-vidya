import os
import re
import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader
from typing import List, Dict, Any
from backend.app.core.config import settings

class IngestionService:
    def __init__(self):
        # Initialize ChromaDB Client
        # Using persistent client to save data to disk
        self.chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_DIR)
        
        # Using default SentenceTransformer embedding function (all-MiniLM-L6-v2)
        # It downloads the model locally.
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        self.collection = self.chroma_client.get_or_create_collection(
            name="roadmap_rag_context",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extracts text from a single PDF file using pypdf."""
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            return text
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return ""

    def hybrid_chunking(self, text: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
        """
        Uses a heuristic approach to split by sections first, then by size.
        Targeting larger semantic chunks.
        """
        # 1. Normalize
        text = re.sub(r'\n+', '\n', text)
        
        # 2. Split by common section headers (Module, Week, Chapter)
        # This regex looks for patterns like "Module 1:", "Week 2", "Chapter 5"
        # and splits BEFORE them to keep the header with the content.
        pattern = r'(?=\n(?:Module|Week|Chapter|Section)\s+\d+)'
        sections = re.split(pattern, text)
        
        chunks = []
        for section in sections:
            if not section.strip(): continue
            
            # If section is huge, split it further by token/char count
            if len(section) > chunk_size:
                sub_chunks = self._sliding_window_split(section, chunk_size, overlap)
                chunks.extend(sub_chunks)
            else:
                chunks.append(section.strip())
                
        return chunks

    def _sliding_window_split(self, text: str, size: int, overlap: int) -> List[str]:
        """Simple overlapping character/word split fallback."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + size
            chunks.append(text[start:end])
            start = end - overlap
        return chunks

    def enrich_metadata(self, filename: str, text_chunk: str) -> Dict[str, Any]:
        """Infers metadata tags based on content and filename."""
        meta = {"source_file": filename}
        
        # Doc Type
        lower_name = filename.lower()
        if "roadmap" in lower_name:
            meta["document_type"] = "roadmap"
        elif "certification" in lower_name:
            meta["document_type"] = "certification"
        elif "university" in lower_name or "master" in lower_name:
            meta["document_type"] = "university"
        else:
            meta["document_type"] = "general"
            
        # Role Focus
        blob = (filename + " " + text_chunk).lower()
        if "data" in blob and "science" in blob:
            meta["role_focus"] = "data_scientist"
        elif "python" in blob or "backend" in blob or "django" in blob or "fastapi" in blob:
            meta["role_focus"] = "backend_dev"
        elif "ai" in blob or "artificial intelligence" in blob:
            meta["role_focus"] = "ai_engineer"
        else:
            meta["role_focus"] = "general"

        # Level
        if "master" in lower_name or "advanced" in blob:
            meta["level"] = "advanced"
        elif "beginner" in blob or "introduction" in blob:
            meta["level"] = "beginner"
        else:
            meta["level"] = "intermediate"
            
        return meta

    def ingest_directory(self):
        """Main execution flow."""
        files = [f for f in os.listdir(settings.DATA_RAG_DIR) if f.endswith('.pdf')]
        print(f"Found {len(files)} PDFs in {settings.DATA_RAG_DIR}")
        
        total_chunks = 0
        
        for f in files:
            path = os.path.join(settings.DATA_RAG_DIR, f)
            print(f"Processing: {f}")
            
            raw_text = self.extract_text_from_pdf(path)
            if not raw_text:
                print(f"Skipping empty or unreadable: {f}")
                continue
            
            chunks = self.hybrid_chunking(raw_text)
            
            # Prepare batch for Chroma
            ids = []
            documents = []
            metadatas = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{f}_chunk_{i}"
                meta = self.enrich_metadata(f, chunk)
                
                ids.append(chunk_id)
                documents.append(chunk)
                metadatas.append(meta)
            
            if documents:
                self.collection.upsert(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
                print(f"  -> Indexed {len(documents)} chunks.")
                total_chunks += len(documents)
        
        print(f"--- Ingestion Complete. Total Chunks: {total_chunks} ---")

if __name__ == "__main__":
    svc = IngestionService()
    svc.ingest_directory()
