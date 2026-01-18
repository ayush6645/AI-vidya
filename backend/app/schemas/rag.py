from pydantic import BaseModel

class VideoChatRequest(BaseModel):
    video_id: str
    question: str

class VideoChatResponse(BaseModel):
    answer: str
    source: str
    chunks_used: int = 0
