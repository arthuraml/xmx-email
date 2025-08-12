"""
Endpoints para processamento de e-mails
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Optional, Dict, Any, List
from loguru import logger

from ...core.config import settings
from ...core.security import verify_api_key
from ...models.email import EmailInput, EmailBatch
from ...models.processing import EmailProcessingResponse
from ...services.processing_service import processing_service

# Router para endpoints de e-mail
router = APIRouter()


@router.post(
    "/process",
    response_model=EmailProcessingResponse,
    summary="Processar um e-mail",
    description="Classifica o e-mail e busca dados de rastreamento se necessário"
)
async def process_email(
    email: EmailInput,
    custom_prompt: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
) -> EmailProcessingResponse:
    """
    Processa um e-mail: classifica e busca rastreamento automaticamente
    
    Este endpoint:
    1. Classifica o e-mail via Gemini (suporte/rastreamento)
    2. Se for rastreamento, busca automaticamente no MySQL
    3. Retorna resposta consolidada com classificação e dados
    
    Args:
        email: Dados do e-mail para processar
        custom_prompt: Prompt customizado (opcional)
    
    Returns:
        Resultado unificado com classificação e dados de rastreamento
    """
    try:
        logger.info(f"Processing email {email.email_id} from {email.from_address}")
        
        # Processa com serviço unificado
        result = await processing_service.process_email(
            email=email,
            custom_prompt=custom_prompt
        )
        
        logger.info(
            f"Email {email.email_id} processed - "
            f"Support: {result.classification.is_support}, "
            f"Tracking: {result.classification.is_tracking}, "
            f"Confidence: {result.classification.confidence:.2f}"
        )
        
        if result.tracking_data and result.tracking_data.found:
            logger.info(f"Found {len(result.tracking_data.orders)} tracking records")
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing email: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing email: {str(e)}"
        )


@router.post(
    "/process-batch",
    summary="Processar múltiplos e-mails",
    description="Processa um lote de e-mails com classificação e rastreamento"
)
async def process_email_batch(
    batch: EmailBatch,
    background_tasks: BackgroundTasks,
    custom_prompt: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Processa múltiplos e-mails em lote
    
    Args:
        batch: Lote de e-mails para processar
        system_prompt: Prompt customizado (opcional)
    
    Returns:
        Status do processamento em lote
    """
    import uuid
    from datetime import datetime
    
    # Gera ID do job
    job_id = str(uuid.uuid4())
    
    # Se processamento assíncrono solicitado
    if batch.process_async:
        # Adiciona tarefa em background
        background_tasks.add_task(
            _process_batch_background,
            job_id=job_id,
            emails=batch.emails,
            custom_prompt=custom_prompt,
            webhook_url=batch.webhook_url
        )
        
        # Retorna status inicial
        return {
            "job_id": job_id,
            "total_emails": len(batch.emails),
            "status": "queued",
            "message": "Batch processing started in background"
        }
    
    # Processamento síncrono
    logger.info(f"Processing batch of {len(batch.emails)} emails")
    
    results = await processing_service.process_batch(
        emails=batch.emails,
        max_concurrent=settings.MAX_CONCURRENT_REQUESTS
    )
    
    # Conta sucessos e falhas
    succeeded = sum(1 for r in results if not r.error)
    failed = sum(1 for r in results if r.error)
    
    return {
        "job_id": job_id,
        "total_emails": len(batch.emails),
        "processed": len(results),
        "succeeded": succeeded,
        "failed": failed,
        "status": "completed",
        "results": [r.model_dump() for r in results]
    }


@router.get(
    "/{email_id}/status",
    summary="Verificar status de processamento",
    description="Verifica o status de processamento de um e-mail específico"
)
async def get_email_status(
    email_id: str,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Verifica status de processamento de um e-mail
    
    Por enquanto, retorna um placeholder.
    No futuro, consultará o banco de dados.
    """
    # TODO: Implementar consulta ao banco
    return {
        "email_id": email_id,
        "status": "not_found",
        "message": "Funcionalidade de consulta de status será implementada em breve"
    }


@router.post(
    "/test-connection",
    summary="Testar conexões",
    description="Verifica conexões com Gemini e MySQL"
)
async def test_connections(
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Testa conexões com Gemini e MySQL
    """
    try:
        from ...services.gemini_service import gemini_service
        from ...services.mysql_service import mysql_service
        
        gemini_connected = await gemini_service.test_connection()
        mysql_connected = await mysql_service.test_connection()
        
        return {
            "gemini": {
                "connected": gemini_connected,
                "model": settings.GEMINI_MODEL
            },
            "mysql": {
                "connected": mysql_connected,
                "database": settings.MYSQL_DATABASE if mysql_connected else None
            },
            "status": "ok" if (gemini_connected and mysql_connected) else "partial",
            "message": "All connections working" if (gemini_connected and mysql_connected) else "Some connections failed"
        }
        
    except Exception as e:
        logger.error(f"Error testing connections: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Error testing connections"
        }


# Função auxiliar para processamento em background
async def _process_batch_background(
    job_id: str,
    emails: List[EmailInput],
    custom_prompt: Optional[str],
    webhook_url: Optional[str]
):
    """
    Processa lote em background
    """
    logger.info(f"Starting background processing for job {job_id}")
    
    try:
        # Processa e-mails
        results = await processing_service.process_batch(
            emails=emails
        )
        
        # Se webhook fornecido, envia resultado
        if webhook_url:
            import httpx
            async with httpx.AsyncClient() as client:
                try:
                    await client.post(
                        webhook_url,
                        json={
                            "job_id": job_id,
                            "status": "completed",
                            "results": [r.model_dump() for r in results]
                        },
                        timeout=30.0
                    )
                except Exception as e:
                    logger.error(f"Erro ao enviar webhook: {e}")
        
        logger.info(f"Job {job_id} concluído com sucesso")
        
    except Exception as e:
        logger.error(f"Erro no job {job_id}: {e}")
        
        # Tenta enviar erro via webhook
        if webhook_url:
            import httpx
            async with httpx.AsyncClient() as client:
                try:
                    await client.post(
                        webhook_url,
                        json={
                            "job_id": job_id,
                            "status": "failed",
                            "error": str(e)
                        },
                        timeout=30.0
                    )
                except:
                    pass