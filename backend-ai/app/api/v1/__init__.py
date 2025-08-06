"""
API v1 routers
"""

from .emails import router as emails_router
from .health import router as health_router
from .classification import router as classification_router
from .tracking import router as tracking_router
from .response_generation import router as response_generation_router

__all__ = [
    "emails_router",
    "health_router",
    "classification_router",
    "tracking_router",
    "response_generation_router"
]