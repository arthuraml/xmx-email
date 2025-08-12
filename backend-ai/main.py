"""
XMX Email AI Backend - Main Application
Processamento inteligente de e-mails com Google Gemini
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from loguru import logger

# Import local modules
from app.core.config import settings
from app.api.v1 import (
    emails_router, 
    health_router,
    response_generation_router
)
from app.db.supabase import init_supabase
from app.core.gemini import init_gemini_client
from app.services.mysql_service import mysql_service

# Configure logger
logger.add(
    "logs/app.log",
    rotation="500 MB",
    retention="10 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level=settings.LOG_LEVEL
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplica��o
    """
    # Startup
    logger.info("Iniciando XMX Email AI Backend...")
    
    # Inicializar conex�es
    await init_supabase()
    init_gemini_client()
    
    # Inicializar MySQL
    try:
        await mysql_service.initialize()
        logger.info("MySQL service initialized")
    except Exception as e:
        logger.warning(f"MySQL initialization failed (non-critical): {e}")
    
    logger.info("Backend iniciado com sucesso!")
    
    yield
    
    # Shutdown
    logger.info("Encerrando XMX Email AI Backend...")
    
    # Fechar conexão MySQL
    await mysql_service.close()


# Criar aplica��o FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description="Backend de processamento inteligente de e-mails com Google Gemini AI",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar Rate Limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Incluir rotas
app.include_router(
    health_router,
    prefix="/api/v1",
    tags=["health"]
)

app.include_router(
    emails_router,
    prefix="/api/v1/emails",
    tags=["emails"]
)

# Endpoints removidos (integrados ao processamento):
# - /api/v1/classification/* (agora parte de /emails/process)
# - /api/v1/tracking/* (agora parte de /emails/process)

app.include_router(
    response_generation_router,
    prefix="/api/v1/response",
    tags=["response"]
)

# Root endpoint
@app.get("/")
async def root():
    """
    Endpoint raiz - informa��es b�sicas da API
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Backend de processamento inteligente de e-mails",
        "docs": "/api/docs",
        "health": "/api/v1/health"
    }

# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    logger.error(f"ValueError: {exc}")
    return {
        "error": "Valor inv�lido",
        "detail": str(exc)
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Erro n�o tratado: {exc}")
    return {
        "error": "Erro interno do servidor",
        "detail": "Um erro inesperado ocorreu. Por favor, tente novamente."
    }

# Middleware para logging de requests
@app.middleware("http")
async def log_requests(request, call_next):
    """
    Log de todas as requisi��es
    """
    import time
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Tempo: {process_time:.3f}s"
    )
    
    return response


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )