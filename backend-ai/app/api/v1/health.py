"""
Health check endpoints
"""

from fastapi import APIRouter
from datetime import datetime
from typing import Dict, Any

from ...core.config import settings
from ...core.gemini import test_gemini_connection

router = APIRouter()


@router.get(
    "/health",
    summary="Health check",
    description="Verifica se o serviço está funcionando"
)
async def health_check() -> Dict[str, Any]:
    """
    Health check básico
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT
    }


@router.get(
    "/health/detailed",
    summary="Health check detalhado",
    description="Verifica status de todas as dependências"
)
async def detailed_health_check() -> Dict[str, Any]:
    """
    Health check detalhado com status de dependências
    """
    # Testa conexão com Gemini
    try:
        gemini_status = test_gemini_connection()
        gemini_error = None
    except Exception as e:
        gemini_status = False
        gemini_error = str(e)
    
    # Status geral
    all_healthy = gemini_status
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT,
        "dependencies": {
            "gemini": {
                "status": "healthy" if gemini_status else "unhealthy",
                "model": settings.GEMINI_MODEL,
                "error": gemini_error
            },
            "supabase": {
                "status": "not_implemented",
                "url": settings.SUPABASE_URL,
                "message": "Conexão com Supabase será implementada"
            }
        },
        "config": {
            "debug": settings.DEBUG,
            "cors_origins": settings.get_cors_origins(),
            "rate_limit": {
                "requests": settings.RATE_LIMIT_REQUESTS,
                "period": settings.RATE_LIMIT_PERIOD
            }
        }
    }


@router.get(
    "/ready",
    summary="Readiness probe",
    description="Verifica se o serviço está pronto para receber requisições"
)
async def readiness_probe() -> Dict[str, Any]:
    """
    Readiness probe para Kubernetes
    """
    # Verifica se Gemini está conectado
    try:
        gemini_ready = test_gemini_connection()
    except:
        gemini_ready = False
    
    if not gemini_ready:
        return {
            "ready": False,
            "reason": "Gemini API não está acessível"
        }
    
    return {
        "ready": True,
        "timestamp": datetime.utcnow().isoformat()
    }