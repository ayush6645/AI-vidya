from pydantic import BaseModel
from typing import List, Optional, Any

class GeneratePlanRequest(BaseModel):
    topic: str
    difficulty: str
    timeline: int

class RoadmapRequest(BaseModel):
    topic: str
    level: Optional[str] = "Beginner"
    duration: Optional[int] = 3

class Lesson(BaseModel):
    day_of_plan: int
    topic: str
    description: str
    Youtube_keywords: Optional[str] = None
    moduleId: Optional[str] = None
    is_completed: Optional[bool] = False
    youtube_link: Optional[str] = None
    status: Optional[str] = None

class Module(BaseModel):
    module_title: str
    module_number: int
    lessons: List[Lesson]

class PlanData(BaseModel):
    plan_title: str
    difficulty_level: Optional[str] = None
    total_duration_months: Optional[int] = None
    modules: List[Module]

class SavePlanRequest(BaseModel):
    plan_data: PlanData
    userId: str

class PlanResponse(BaseModel):
    status: str
    plan_id: Optional[str] = None
    message: Optional[str] = None

class VideoResponse(BaseModel):
    status: str
    video_url: Optional[str] = None
    from_cache: Optional[bool] = None
    message: Optional[str] = None

class CompletionRequest(BaseModel):
    is_completed: bool
    plan_id: str

class NoteRequest(BaseModel):
    title: str
    body: str
    lessonId: str

class QuizOption(BaseModel):
    question: str
    options: List[str]
    answer: str

class QuizRequest(BaseModel):
    lesson_id: str

class QuizSubmission(BaseModel):
    score: int
    total: int
    planId: str

class SummaryQuizResponse(BaseModel):
    status: str
    summary: Optional[str] = None
    quiz: Optional[List[QuizOption]] = None
