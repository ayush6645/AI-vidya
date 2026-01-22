from fastapi import APIRouter
from backend.app.api.v1.endpoints import auth, users, plans, rag, tts

api_router = APIRouter()
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(users.router, tags=["users"])
api_router.include_router(plans.router, tags=["plans"])
api_router.include_router(rag.router, prefix="/api", tags=["rag"])
api_router.include_router(tts.router, prefix="/api/tts", tags=["tts"])
