print("Starting Application...")
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from backend.app.core.config import settings, init_firebase
from backend.app.api.v1.api import api_router
from backend.app.core.templates import templates

# Initialize App
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs"
)

# Middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

# Fix for Azure: Trust proxy headers (X-Forwarded-Proto, X-Forwarded-For)
@app.middleware("http")
async def add_proxy_headers(request: Request, call_next):
    # Azure sets X-Forwarded-Proto to tell us if the original request was HTTPS
    if "x-forwarded-proto" in request.headers:
        request.scope["scheme"] = request.headers["x-forwarded-proto"]
    response = await call_next(request)
    return response

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Static Files
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

# Routes
app.include_router(api_router) # Auto-includes /api prefix if defined in api.py, but I didn't there.
# To match Flask structure where some routes are root and some are /api,
# I aggregated them. 
# HTML routes in 'plans' and 'users' are at root paths (e.g. /dashboard).
# API routes are mixed.
# Ideally, I should separate them, but for migration, I just included them directly.

@app.on_event("startup")
async def startup_event():
    init_firebase()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    user_id = request.session.get("user_id")
    if user_id:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8080, reload=True)
