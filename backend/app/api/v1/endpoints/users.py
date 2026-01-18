from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from backend.app.services.db_service import db_service
from backend.app.schemas.user import UpdateProfileRequest, ChangePasswordRequest, DashboardResponse
from backend.app.core.templates import templates
from backend.app.core.deps import get_current_user_required
from werkzeug.security import check_password_hash, generate_password_hash

router = APIRouter()

# --- API Endpoints ---

@router.get("/dashboard-data", response_model=DashboardResponse)
async def get_dashboard_data(request: Request, user_id: str = Depends(get_current_user_required)):
    plans = await db_service.get_user_plans(user_id)
    last_plan_id = plans[0]['id'] if plans else None
    
    return {
        "status": "success",
        "data": {
            "name": request.session.get('name', 'User'),
            "plan_count": len(plans),
            "completed_topics_count": await db_service.get_completed_lessons_count(user_id),
            "last_plan_id": last_plan_id,
            "xp_points": 1250, # Could be calculated from completed lessons * 50 + quiz scores * 10
            "day_streak": 7,
            "quiz_accuracy": await db_service.get_quiz_average(user_id),
            "level": 3
        }
    }

@router.post("/profile/update")
async def update_profile(request: Request, user_id: str = Depends(get_current_user_required)):
    content_type = request.headers.get('content-type', '')
    if 'application/json' in content_type:
        data = await request.json()
    else:
        form = await request.form()
        data = dict(form)

    update_data = {}
    if data.get('first_name'): update_data['first_name'] = data.get('first_name')
    if data.get('last_name'): update_data['last_name'] = data.get('last_name')
    if data.get('phone_number'): update_data['phone_number'] = data.get('phone_number')
    if data.get('username'): update_data['username'] = data.get('username')

    if update_data:
        await db_service.update_user(user_id, update_data)
        if update_data.get('first_name'):
            request.session['name'] = f"{update_data['first_name']} {update_data.get('last_name', '')}"
    
    if 'application/json' not in content_type:
        return RedirectResponse(url="/edit-profile", status_code=303)

    return {"status": "success", "message": "Profile updated"}

@router.post("/settings/change-password")
async def change_password(data: ChangePasswordRequest, user_id: str = Depends(get_current_user_required)):
    user = await db_service.get_user(user_id)
    if not check_password_hash(user.get('password_hash'), data.current_password):
        raise HTTPException(status_code=403, detail="Wrong password")
        
    new_hash = generate_password_hash(data.new_password)
    await db_service.update_user(user_id, {'password_hash': new_hash})
    return {"status": "success", "message": "Password updated"}

@router.post("/settings/delete-account")
async def delete_account(request: Request, user_id: str = Depends(get_current_user_required)):
    plans = await db_service.get_user_plans(user_id)
    for plan in plans:
        await db_service.delete_plan_full(plan['id'], user_id)
    await db_service.delete_user(user_id)
    request.session.clear()
    return {"status": "success", "message": "Account deleted"}

@router.post("/settings/delete-all-plans")
async def delete_all_plans(user_id: str = Depends(get_current_user_required)):
    plans = await db_service.get_user_plans(user_id)
    for plan in plans:
        await db_service.delete_plan_full(plan['id'], user_id)
    return {"status": "success", "message": "All plans deleted"}

# --- HTML Routes (Web) ---

@router.get("/dashboard", response_class=HTMLResponse)
async def view_dashboard(request: Request):
    # For HTML, we can check cookie manually or use dependency (which might raise JSON 401).
    # Better to check manually and redirect.
    token = request.cookies.get("access_token")
    if not token: return RedirectResponse(url="/login")
    
    from backend.app.core.security import security
    user_id = security.verify_token(token)
    if not user_id: return RedirectResponse(url="/login")
    
    # Fetch data for "Complete Potential"
    plans = await db_service.get_user_plans(user_id)
    completed_topics = await db_service.get_completed_lessons_count(user_id)
    quiz_acc = await db_service.get_quiz_average(user_id)
    last_plan = plans[0] if plans else None
    
    # Get User Stats for XP, Streak, and Level
    stats = await db_service.get_user_stats(user_id)
    user = await db_service.get_user(user_id)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "name": request.session.get("name") or (user.get('first_name') if user else 'User'),
        "plan_count": len(plans),
        "completed_topics_count": completed_topics,
        "quiz_accuracy": quiz_acc,
        "last_plan": last_plan,
        "xp_points": stats.get('xp', 0),
        "level": stats.get('level', 1),
        "day_streak": stats.get('streak', 0)
    })

@router.get("/edit-profile", response_class=HTMLResponse)
async def view_edit_profile(request: Request):
    token = request.cookies.get("access_token")
    if not token: return RedirectResponse(url="/login")
    
    # We need the user ID. We could decode token or trust session for UI.
    # Let's decode to be safe/stateless-ish.
    from backend.app.core.security import security
    user_id = security.verify_token(token)
    if not user_id: return RedirectResponse(url="/login")

    user = await db_service.get_user(user_id)
    return templates.TemplateResponse("edit_profile.html", {"request": request, "user": user})

@router.get("/settings", response_class=HTMLResponse)
async def view_settings(request: Request):
    token = request.cookies.get("access_token")
    if not token: return RedirectResponse(url="/login")
    
    from backend.app.core.security import security
    user_id = security.verify_token(token)
    if not user_id: return RedirectResponse(url="/login")
    
    user = await db_service.get_user(user_id)
    return templates.TemplateResponse("settings.html", {"request": request, "user": user})
