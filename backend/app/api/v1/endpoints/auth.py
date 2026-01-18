from fastapi import APIRouter, Request, HTTPException, Response, status
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from backend.app.schemas.auth import AuthCheckResponse
from backend.app.services.db_service import db_service
from backend.app.core.security import security
from backend.app.core.deps import get_current_user
from werkzeug.security import check_password_hash, generate_password_hash
from backend.app.core.config import settings
from backend.app.core.templates import templates

router = APIRouter()

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/login")
async def login(request: Request, response: Response):
    # Handle both JSON and Form (Legacy Migration)
    content_type = request.headers.get('content-type', '')
    if 'application/json' in content_type:
        data = await request.json()
    else:
        form = await request.form()
        data = dict(form)

    # Validate manual extraction
    login_type = data.get('loginType')
    login_value = data.get('login_value', '').strip()
    auth_type = data.get('authType')
    auth_value = data.get('auth_value', '').strip()

    print(f"DEBUG: Login attempt: Type={login_type}, Value={login_value}")

    if not all([login_type, login_value, auth_type, auth_value]):
        raise HTTPException(status_code=400, detail="Missing fields")

    # Mapping Flask logic
    field_map = {
        'loginUsername': 'username',
        'loginEmail': 'email', 
        'loginPhone': 'phone_number'
    }
    
    db_field = field_map.get(login_type)
    if not db_field:
        raise HTTPException(status_code=400, detail="Invalid login type")

    # DB Lookup
    user = None
    if db_field == 'email':
        # Normalize to lowercase
        user = await db_service.get_user_by_email(login_value.lower())
    elif db_field == 'username':
        # Don't lower username blindly unless we know we save them lowered.
        # But safest is to search exact first?
        # Let's assume username is case sensitive for now, but email IS NOT.
        user = await db_service.get_user_by_username(login_value)
    else:
        raise HTTPException(status_code=400, detail="Login type not supported")

    if not user:
        print(f"DEBUG: User not found for {db_field}={login_value}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Debug Password Hash (SAFETY: Do not log real passwords in prod, but for debug here we check status)
    stored_hash = user.get('password_hash', '')
    print(f"DEBUG: User found. ID={user.get('id')}. Checking password...")
    
    if not check_password_hash(stored_hash, auth_value):
        print("DEBUG: Password mismatch.")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    print("DEBUG: Password matched. Generating token...")

    # Generate Token
    # Critical Fix: Ensure ID is present.
    user_id = user.get('id')
    if not user_id:
        # Fallback if ID missing in dict but using email/username as ID.
        if db_field == 'email': user_id = login_value.lower()
        elif db_field == 'username': user_id = login_value
        print(f"DEBUG: ID missing in user dict. Using fallback: {user_id}")
        
    access_token = security.create_access_token(user_id)
    
    # Set Cookie for Browser Support (HttpOnly for security)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=60 * 60 * 24 * 7, # 7 days
        samesite='lax'
    )
    
    # Store minimal user info in session
    request.session['name'] = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()

    return {
        "status": "success",
        "message": "Login successful!",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "username": user.get('username'),
            "name": request.session['name']
        }
    }

@router.post("/register")
async def register(request: Request):
    content_type = request.headers.get('content-type', '')
    if 'application/json' in content_type:
        data = await request.json()
    else:
        form = await request.form()
        data = dict(form)
    
    email = data.get('email', '').strip().lower() # Lowercase email
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    confirm = data.get('confirm_password', '').strip()
    
    if not all([email, username, password, confirm]):
        raise HTTPException(status_code=400, detail="Missing fields")

    if await db_service.get_user_by_email(email):
        raise HTTPException(status_code=400, detail="Email already exists")
    
    if await db_service.get_user_by_username(username):
        raise HTTPException(status_code=400, detail="Username already taken")

    if password != confirm:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    hashed = generate_password_hash(password)
    
    user_data = {
        'first_name': data.get('first_name', '').strip(),
        'last_name': data.get('last_name', '').strip(),
        'date_of_birth': data.get('date_of_birth'),
        'education': data.get('education'),
        'email': email,
        'phone_number': data.get('phone_number'),
        'username': username,
        'password_hash': hashed
    }
    
    await db_service.create_user(email, user_data)
    
    if 'application/json' not in content_type:
        return RedirectResponse(url="/login", status_code=303)
        
    return {"status": "success", "message": "Registration successful"}

@router.get("/logout")
async def logout(request: Request, response: Response):
    request.session.clear() # Clear legacy session
    response.delete_cookie("access_token") # Clear JWT cookie
    return RedirectResponse(url="/login")

@router.get("/check-auth", response_model=AuthCheckResponse)
async def check_auth(request: Request):
    # Try getting from session first (legacy/UI)
    user_id = request.session.get('user_id') 
    
    # If not in session, try JWT from cookie/header (via dependency if we wired it here)
    # For now, let's keep this simple as a session check for the UI.
    # Proper API auth check uses the dependency on protected routes.
    
    if user_id:
        return {
            "status": "success", 
            "authenticated": True, 
            "user": {"id": user_id, "username": request.session.get('username'), "name": request.session.get('name')}
        }
    return {"status": "success", "authenticated": False}
