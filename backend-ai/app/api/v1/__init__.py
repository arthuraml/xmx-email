"""
API v1 routers
"""

from .emails import router as emails_router
from .health import router as health_router

__all__ = [
    "emails_router",
    "health_router"
]