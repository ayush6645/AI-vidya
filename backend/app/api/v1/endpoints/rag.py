from fastapi import APIRouter, HTTPException, Depends, Request
from backend.app.schemas.rag import VideoChatResponse, VideoChatRequest
from backend.app.services.video_rag_service import video_rag_service
from backend.app.core.deps import get_current_user_required

router = APIRouter()

@router.post("/video-chat", response_model=VideoChatResponse)
async def chat_with_video(
    payload: VideoChatRequest,
    current_user: dict = Depends(get_current_user_required)
):
    """
    Chat with a specific YouTube video context.
    """
    try:
        response = await video_rag_service.chat(payload.video_id, payload.question)
        return response
    except Exception as e:
        print(f"RAG ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))
