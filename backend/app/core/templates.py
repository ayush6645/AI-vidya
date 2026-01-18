from fastapi.templating import Jinja2Templates
from backend.app.core.config import settings

templates = Jinja2Templates(directory=settings.TEMPLATE_DIR)
