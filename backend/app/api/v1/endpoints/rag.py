from fastapi import APIRouter, HTTPException, Depends, Request
from backend.app.schemas.rag import VideoChatResponse
from backend.app.services.video_rag_service import video_rag_service
from backend.app.core.deps import get_current_user_required

router = APIRouter()

@router.post("/video-chat", response_model=VideoChatResponse)
async def chat_with_video(
    request: Request,
    # payload: VideoChatRequest,
    current_user: dict = Depends(get_current_user_required)
):
    """
    Chat with a specific YouTube video context.
    """
    try:
        payload_dict = await request.json()
        print(f"DEBUG RAG PAYLOAD: {payload_dict}")
        # Manually validate
        video_id = payload_dict.get('video_id')
        question = payload_dict.get('question')
        
        if not video_id or not question:
             raise HTTPException(status_code=400, detail="Missing video_id or question")
             
        response = await video_rag_service.chat(video_id, question)
        return response
    except Exception as e:
        print(f"RAG ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))
