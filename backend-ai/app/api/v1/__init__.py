"""
API v1 routers
"""

from .emails import router as emails_router
from .health import router as health_router
from .response_generation import router as response_generation_router
from .analytics import router as analytics_router

# Routers removidos (funcionalidade integrada ao emails_router):
# - classification_router (agora parte de /emails/process)
# - tracking_router (agora parte de /emails/process)

__all__ = [
    "emails_router",
    "health_router",
    "response_generation_router",
    "analytics_router"
]