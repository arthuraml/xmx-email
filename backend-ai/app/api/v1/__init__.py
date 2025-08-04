"""
API v1 routers
"""

from .emails import router as emails_router
from .prompts import router as prompts_router
from .analytics import router as analytics_router
from .health import router as health_router

__all__ = [
    "emails_router",
    "prompts_router", 
    "analytics_router",
    "health_router"
]