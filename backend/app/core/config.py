import os
import json
import logging
from typing import Optional
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Ai-Vidya"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.environ.get("FLASK_SECRET_KEY", "your-default-secret-key-123!")
    
    # External APIs
    GOOGLE_API_KEY: Optional[str] = os.environ.get("GOOGLE_API_KEY")
    YOUTUBE_API_KEY: Optional[str] = os.environ.get("YOUTUBE_API_KEY")
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # Go up 3 levels from core/config.py to root
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(BASE_DIR)))
    
    TEMPLATE_DIR = os.path.join(ROOT_DIR, 'Web_App')
    STATIC_DIR = os.path.join(ROOT_DIR, 'Web_App')
    
    # RAG Settings
    # RAG Settings
    DATA_RAG_DIR: str = r"E:\AI_Edu_Bot_Project\data_rag"
    CHROMA_DB_DIR: str = os.path.join(ROOT_DIR, "backend", "data", "chroma_db")
    
    # Cloud Run specific overwrite: Use /tmp because system is read-only
    if os.environ.get("K_SERVICE") or os.environ.get("PORT"):
         CHROMA_DB_DIR = "/tmp/chroma_db"
         DATA_RAG_DIR = "/tmp/data_rag"

    PROMPTS_DIR: str = os.path.join(ROOT_DIR, "backend", "app", "prompts")

settings = Settings()

# Firebase Initialization
db = None
def init_firebase():
    global db
    if db: return db
    
    try:
        if os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")
        elif os.environ.get('FIREBASE_CREDENTIALS'):
            cred_dict = json.loads(os.environ.get('FIREBASE_CREDENTIALS'))
            cred = credentials.Certificate(cred_dict)
        else:
            logging.warning("No Firebase credentials found!")
            return None

        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        logging.info("Firebase initialized successfully.")
        return db
    except Exception as e:
        logging.error(f"Error initializing Firebase: {e}")
        return None

# Initialize immediately for module-level access, 
# though usage should be via dependency or service.
# REMOVED global call to prevent import-time crashes on Cloud Run
# init_firebase()
