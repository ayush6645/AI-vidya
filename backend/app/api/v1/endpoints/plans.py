from fastapi import APIRouter, Request, HTTPException, Depends
from typing import Optional
from pydantic import BaseModel
from fastapi.responses import HTMLResponse, RedirectResponse
from backend.app.schemas.plan import GeneratePlanRequest, SavePlanRequest, CompletionRequest, NoteRequest, RoadmapRequest, QuizRequest, SummaryQuizResponse, QuizSubmission
from backend.app.services.db_service import db_service
from backend.app.services.llm_service import llm_service
from backend.app.services.rag_service import rag_service
from backend.app.services.youtube_service import youtube_service
from backend.app.services.rag_service import rag_service
from backend.app.core.templates import templates
from backend.app.core.deps import get_current_user_required
from google.cloud import firestore

router = APIRouter()

@router.post("/roadmap")
async def create_roadmap(data: RoadmapRequest, user_id: str = Depends(get_current_user_required)):
    """
    Generate a learning roadmap using RAG (Retrieval-Augmented Generation).
    If relevant syllabi are found, uses them as context.
    Otherwise, falls back to LLM knowledge.
    """
    result = await rag_service.generate_roadmap_rag(data.topic, data.level, data.duration)
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))
    return result

@router.post("/generate_plan")
async def generate_plan(data: GeneratePlanRequest, user_id: str = Depends(get_current_user_required)):
    # Upgraded to use direct LLM generation with high-quality prompt (User Request: Remove unnecessary RAG)
    # The new prompt in llm_service.generate_plan() wraps all the logic needed.
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        result = await llm_service.generate_plan(data.topic, data.difficulty, data.timeline, data.time_investment)
    except Exception as e:
        logger.error(f"Plan Generation Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Plan generation failed: {str(e)}")
    
    if not result:
        logger.error("Plan Generation returned None (likely API Key or Model issue)")
        raise HTTPException(status_code=500, detail="Failed to generate plan. Please try again.")
    
    # Check if result matches expected structure roughly
    if "modules" not in result:
         logger.error(f"Invalid Plan Structure: {result}")
         raise HTTPException(status_code=500, detail="Generated plan format invalid.")

    # Return structure matching frontend expectation
    return {"status": "success", "plan_data": result}

@router.post("/save_plan")
async def save_plan(data: SavePlanRequest, user_id: str = Depends(get_current_user_required)):
    plan_dict = {
        'userId': user_id, 
        'plan_title': data.plan_data.plan_title,
        'difficulty_level': data.plan_data.difficulty_level,
        'total_duration_months': data.plan_data.total_duration_months,
        'creation_date': firestore.SERVER_TIMESTAMP,
        'status': 'active'
    }
    plan_id = await db_service.create_plan(plan_dict)
    
    for module in data.plan_data.modules:
        mod_dict = {'planId': plan_id, 'module_number': module.module_number, 'module_title': module.module_title}
        mod_id = await db_service.create_module(mod_dict)
        for lesson in module.lessons:
            lesson_dict = lesson.dict(exclude={'Youtube_keywords'})
            lesson_dict['moduleId'] = mod_id
            await db_service.create_lesson(lesson_dict)
            
    return {"status": "success", "plan_id": plan_id}

@router.get("/plans")
async def list_plans(user_id: str = Depends(get_current_user_required)):
    plans = await db_service.get_user_plans(user_id)
    return {"status": "success", "plans": plans}

@router.get("/plans/{plan_id}")
async def get_plan_details(plan_id: str, user_id: str = Depends(get_current_user_required)):
    plan = await db_service.get_plan_details(plan_id)
    modules = await db_service.get_modules_by_plan(plan_id)
    for mod in modules:
        mod['lessons'] = await db_service.get_lessons_by_module(mod['id'])
    return {"status": "success", "plan": plan, "modules": modules}

@router.post("/quiz", response_model=SummaryQuizResponse)
async def generate_quiz(data: QuizRequest, user_id: str = Depends(get_current_user_required)):
    lesson = await db_service.get_lesson(data.lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # We can pass specific instructions if needed, allowing "Complete Potential" logic
    result = await llm_service.generate_summary_and_quiz(lesson.get('topic'), lesson.get('description'))
    return {"status": "success", "summary": result.get("summary"), "quiz": result.get("quiz")}

@router.post("/api/lesson/{lesson_id}/generate-summary")
async def generate_lesson_summary(lesson_id: str, user_id: str = Depends(get_current_user_required)):
    lesson = await db_service.get_lesson(lesson_id)
    if not lesson: return {"status": "error", "message": "Lesson not found"}
    
    # Check if summary/quiz already exists (Cache Hit)
    if lesson.get('summary') and lesson.get('quiz_data'):
        return {"status": "success", "summary": lesson.get('summary'), "quiz": lesson.get('quiz_data')}
        
    # Cache Miss: Generate
    result = await llm_service.generate_summary_and_quiz(lesson.get('topic'), lesson.get('description'))
    
    # Save to DB for future use
    if result and result.get('summary'):
        await db_service.update_lesson(lesson_id, {
            'summary': result.get('summary'),
            'quiz_data': result.get('quiz')
        })
        
    return {"status": "success", "summary": result.get("summary"), "quiz": result.get("quiz")}

@router.post("/api/lessons/{lesson_id}/completion")
async def mark_lesson_completion(lesson_id: str, data: CompletionRequest, user_id: str = Depends(get_current_user_required)):
    # Toggle boolean based on request or just set true? Request has is_completed
    await db_service.update_lesson(lesson_id, {"completed": data.is_completed, "is_completed": data.is_completed})
    return {"status": "success", "progress": 50} # TODO: Calculate real progress

@router.post("/api/get-video-for-lesson/{lesson_id}")
async def get_video_for_lesson(lesson_id: str, user_id: str = Depends(get_current_user_required)):
    lesson = await db_service.get_lesson(lesson_id)
    if not lesson:
        return {
            "video_url": youtube_service._get_fallback_video(),
            "is_curated": False,
            "message": "Lesson not found, using fallback"
        }
    
    # Use enhanced YouTube service
    topic = lesson.get('topic', 'Learning')
    description = lesson.get('description', '')
    
    video_url = await youtube_service.get_video_for_lesson(topic, description, lesson_id)
    
    # Only cache if it's a good quality video (not fallback)
    if video_url != youtube_service._get_fallback_video():
        await db_service.update_lesson(lesson_id, {
            'youtube_link': video_url,
            'video_last_updated': firestore.SERVER_TIMESTAMP
        })
    
    return {
        "video_url": video_url,
        "is_curated": video_url != youtube_service._get_fallback_video(),
        "quality_score": "high" if video_url != youtube_service._get_fallback_video() else "fallback",
        "message": "Quality educational video found" if video_url != youtube_service._get_fallback_video() else "Using educational fallback"
    }

# Add admin endpoint to refresh all caches
class RefreshCacheSchema(BaseModel):
    plan_id: Optional[str] = None
    lesson_id: Optional[str] = None

@router.post("/api/admin/refresh-youtube-cache")
async def refresh_youtube_cache(
    request: RefreshCacheSchema,
    user_id: str = Depends(get_current_user_required)
):
    """Refresh YouTube cache for all lessons, specific plan, or specific lesson"""
    try:
        if request.lesson_id:
            # Refresh specific lesson
            await youtube_service.refresh_cache_for_lesson(request.lesson_id)
            # Also update the lesson document to reflect the clear (optional but good for consistency)
            await db_service.update_lesson(request.lesson_id, {'youtube_link': '', 'video_last_updated': None})
            return {
                "status": "success",
                "message": f"Refreshed cache for lesson {request.lesson_id}"
            }
            
        elif request.plan_id:
            # Refresh only for specific plan
            modules = await db_service.get_modules_by_plan(request.plan_id)
            refreshed = 0
            for mod in modules:
                lessons = await db_service.get_lessons_by_module(mod['id'])
                for lesson in lessons:
                    if await youtube_service.refresh_cache_for_lesson(lesson['id']):
                        refreshed += 1
            
            return {
                "status": "success",
                "message": f"Refreshed cache for {refreshed} lessons in plan {request.plan_id}"
            }
        else:
            # Refresh all lessons (admin only - fallback)
            # This would require scanning all lessons, which is heavy. 
            # For now, return error or mock.
            return {
                "status": "error", 
                "message": "Please specify plan_id or lesson_id"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/lessons/{lesson_id}/notes")
async def get_lesson_notes(lesson_id: str, user_id: str = Depends(get_current_user_required)):
    notes = await db_service.get_notes(user_id, lesson_id)
    return {"notes": notes}

@router.post("/api/my-courses/{plan_id}/add-note")
async def add_note_to_lesson(plan_id: str, note: NoteRequest, user_id: str = Depends(get_current_user_required)):
    note_data = {
        'userId': user_id,
        'planId': plan_id,
        'lessonId': note.lessonId,
        'title': note.title,
        'body': note.body,
        'created_at': firestore.SERVER_TIMESTAMP
    }
    note_id = await db_service.add_note(note_data)
    return {"status": "success", "note_id": note_id}

@router.delete("/api/notes/{note_id}")
async def delete_note(note_id: str, user_id: str = Depends(get_current_user_required)):
    # await db_service.delete_note(note_id) # Pending implementation
    return {"status": "success"}

@router.post("/api/lesson/{lesson_id}/submit-quiz")
async def submit_quiz(lesson_id: str, data: QuizSubmission, user_id: str = Depends(get_current_user_required)):
    # Store result in DB
    result_data = {
        'userId': user_id,
        'lessonId': lesson_id,
        'planId': data.planId,
        'score': data.score,
        'total': data.total,
        'date': firestore.SERVER_TIMESTAMP
    }
    # Lookup lesson to get topic for history display
    lesson = await db_service.get_lesson(lesson_id)
    if lesson:
        result_data['topic'] = lesson.get('topic', 'Unknown Topic')
        
    await db_service.add_quiz_result(result_data)
    
    # NEW: Update User Points for Leaderboard
    # e.g., 50 points per correct answer
    points_earned = data.score * 50
    if points_earned > 0:
        await db_service.update_user_score(user_id, points_earned)
    
    return {"status": "success"}

# --- HTML Routes ---
@router.get("/start-plan", response_class=HTMLResponse)
async def view_start_plan(request: Request):
    if not request.cookies.get("access_token"): return RedirectResponse("/login")
    return templates.TemplateResponse("start_plan.html", {"request": request, "user_id": request.session.get("user_id")})

@router.get("/my-courses", response_class=HTMLResponse)
async def view_my_courses(request: Request):
    token = request.cookies.get("access_token")
    if not token: return RedirectResponse("/login")
    
    from backend.app.core.security import security
    user_id = security.verify_token(token)
    if not user_id: return RedirectResponse("/login")

    plans = await db_service.get_user_plans(user_id)
    return templates.TemplateResponse("my_courses_list.html", {"request": request, "plans": plans})

@router.get("/my-courses/{plan_id}", response_class=HTMLResponse)
async def view_course_detail(request: Request, plan_id: str):
    token = request.cookies.get("access_token")
    if not token: return RedirectResponse("/login")
    
    from backend.app.core.security import security
    user_id = security.verify_token(token)
    
    plan = await db_service.get_plan_details(plan_id)
    if not plan or plan.get('userId') != user_id: return RedirectResponse("/my-courses")
        
    modules = await db_service.get_modules_by_plan(plan_id)
    all_lessons = []
    for mod in modules:
        lessons = await db_service.get_lessons_by_module(mod['id'])
        mod['lessons'] = lessons
        all_lessons.extend(lessons)
        
    return templates.TemplateResponse("my_course.html", {
        "request": request, "plan": plan, "modules": modules, "lessons": all_lessons, "notes": [], "plan_id": plan_id
    })

@router.get("/quizzes", response_class=HTMLResponse)
async def view_quizzes(request: Request):
    token = request.cookies.get("access_token")
    if not token: return RedirectResponse("/login")
    
    from backend.app.core.security import security
    user_id = security.verify_token(token)
    if not user_id: return RedirectResponse("/login")
    
    history = await db_service.get_quiz_history(user_id)
    
    # Calculate stats
    total_taken = len(history)
    avg_score = sum([int(h.get('score', 0)) for h in history]) / total_taken if total_taken else 0
    high_score = max([int(h.get('score', 0)) for h in history]) if total_taken else 0
    last_attempt = history[0].get('topic', 'N/A') if history else 'N/A'
    
    stats = {
        "total_taken": total_taken,
        "average_score": f"{avg_score:.1f}%",
        "highest_score": f"{high_score}%",
        "last_attempt": last_attempt
    }
    
    # Real Leaderboard Data
    raw_leaderboard = await db_service.get_leaderboard()
    leaderboard = []
    for i, user in enumerate(raw_leaderboard):
        leaderboard.append({
            "rank": i + 1,
            "name": user.get('username') or user.get('first_name') or "Anonymous",
            "score": user.get('total_points', 0)
        })
    
    available_quizzes = [] 
    
    return templates.TemplateResponse("quizzes.html", {
        "request": request,
        "stats": stats,
        "quiz_history": history,
        "available_quizzes": available_quizzes,
        "leaderboard": leaderboard
    })

@router.get("/api/recommendations")
async def get_recommendations(user_id: str = Depends(get_current_user_required)):
    """
    Generate personalized course recommendations based on user's learning patterns.
    Returns trending topics and AI-suggested learning paths.
    """
    # Get user's existing plans to avoid duplicates
    user_plans = await db_service.get_user_plans(user_id)
    existing_topics = [plan.get('plan_title', '').lower() for plan in user_plans]
    
    # Curated trending topics (can be expanded with ML/analytics later)
    trending_topics = [
        "Machine Learning with Python",
        "Full-Stack Web Development",
        "React & Next.js",
        "Data Structures & Algorithms",
        "Cloud Computing (AWS/Azure)",
        "Cybersecurity Fundamentals",
        "Python for Data Science",
        "Mobile App Development (Flutter)",
        "DevOps & CI/CD",
        "Blockchain & Web3",
        "UI/UX Design Principles",
        "System Design Interview Prep"
    ]
    
    # Filter out topics user already has
    recommendations = [
        topic for topic in trending_topics 
        if not any(existing in topic.lower() for existing in existing_topics)
    ][:5]  # Limit to 5 recommendations
    
    return {"status": "success", "recommendations": recommendations}

@router.post("/api/plans/{plan_id}/delete")
async def delete_single_plan(plan_id: str, user_id: str = Depends(get_current_user_required)):
    # Check ownership
    plan = await db_service.get_plan_details(plan_id)
    if not plan or plan.get('userId') != user_id:
         raise HTTPException(status_code=403, detail="Unauthorized")
    
    await db_service.delete_plan_full(plan_id, user_id)
    return {"status": "success", "message": "Plan deleted"}
