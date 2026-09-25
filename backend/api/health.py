from fastapi import APIRouter
from core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/info")
def info():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "source_priority": settings.SOURCE_PRIORITY,
        "match_thresholds": {
            "probable": settings.MATCH_PROBABLE_THRESHOLD,
            "possible": settings.MATCH_POSSIBLE_THRESHOLD,
        },
    }
