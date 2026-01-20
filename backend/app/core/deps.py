from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from backend.app.core.security import security
from backend.app.services.db_service import db_service
from typing import Optional

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

async def get_current_user(request: Request, token: Optional[str] = Depends(oauth2_scheme)):
    # 1. Check Authorization Header (Bearer)
    if not token:
        # 2. Check Cookie (for Web App)
        token = request.cookies.get("access_token")
    
    if not token:
        # 3. Last Resort: Check Session (Legacy/Test Script Support)
        if request.session.get("user_id"):
            return request.session.get("user_id")
            
        # If we are in a purely API context, we might raise 401 here.
        # But because we share this for HTML views (which redirect on None),
        # we return None and let the endpoint/route decide.
        return None

    # Handle "Bearer " prefix if manually set in cookie (rare but possible)
    if token.startswith("Bearer "):
        token = token.split(" ")[1]

    user_id = security.verify_token(token)
    if not user_id:
        return None

    return user_id

async def get_current_user_required(user_id: Optional[str] = Depends(get_current_user)):
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id
