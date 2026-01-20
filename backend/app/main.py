print("Starting Application...")
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
import os
from starlette.middleware.sessions import SessionMiddleware
from backend.app.core.config import settings, init_firebase
from backend.app.api.v1.api import api_router
from backend.app.core.templates import templates

# Initialize App
import logging
import sys

# Configure logging to show up in Azure Log Stream
logging.basicConfig(
    stream=sys.stdout, 
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs"
)

logger.info("Application starting up...")

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

@app.get("/robots.txt", include_in_schema=False)
async def robots():
    return FileResponse(os.path.join(settings.TEMPLATE_DIR, "robots.txt"))

@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap():
    return FileResponse(os.path.join(settings.TEMPLATE_DIR, "sitemap.xml"), media_type="application/xml")

@app.get("/googlef678fb188fe1851a.html", include_in_schema=False)
async def google_verification():
    return FileResponse(os.path.join(settings.TEMPLATE_DIR, "googlef678fb188fe1851a.html"))

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    user_id = request.session.get("user_id")
    if user_id:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port, reload=True)
