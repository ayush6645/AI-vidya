from fastapi import APIRouter, HTTPException, Depends
from backend.app.schemas.rag import VideoChatRequest, VideoChatResponse
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
    if not payload.video_id or not payload.question:
        raise HTTPException(status_code=400, detail="Missing video_id or question")
        
    try:
        # Check if video is indexed, if not index it (handled inside service)
        # Then get answer
        response = await video_rag_service.chat(payload.video_id, payload.question)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
