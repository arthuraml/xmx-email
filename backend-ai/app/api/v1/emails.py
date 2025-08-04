"""
Endpoints para processamento de e-mails
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Optional, Dict, Any, List
from loguru import logger

from ...core.config import settings
from ...core.security import verify_api_key
from ...models.email import EmailInput, EmailBatch
from ...models.response import EmailProcessingResult, BatchProcessingResult, ProcessingStatus
from ...services.gemini_service import gemini_service

# Router para endpoints de e-mail
router = APIRouter()


@router.post(
    "/process",
    response_model=EmailProcessingResult,
    summary="Processar um e-mail",
    description="Analisa um e-mail e decide se deve ser respondido ou ignorado"
)
async def process_email(
    email: EmailInput,
    system_prompt: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
) -> EmailProcessingResult:
    """
    Processa um único e-mail usando Gemini AI
    
    Args:
        email: Dados do e-mail para processar
        system_prompt: Prompt customizado (opcional)
    
    Returns:
        Resultado do processamento com decisão e resposta sugerida
    """
    try:
        logger.info(f"Processando e-mail {email.email_id} de {email.from_address}")
        
        # Processa com Gemini
        result = await gemini_service.process_email(
            email=email,
            system_prompt=system_prompt
        )
        
        logger.info(
            f"E-mail {email.email_id} processado - "
            f"Decisão: {result.decision}, "
            f"Confiança: {result.confidence:.2f}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Erro ao processar e-mail: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar e-mail: {str(e)}"
        )


@router.post(
    "/process-batch",
    response_model=BatchProcessingResult,
    summary="Processar múltiplos e-mails",
    description="Processa um lote de e-mails de forma assíncrona"
)
async def process_email_batch(
    batch: EmailBatch,
    background_tasks: BackgroundTasks,
    system_prompt: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
) -> BatchProcessingResult:
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
            system_prompt=system_prompt,
            webhook_url=batch.webhook_url
        )
        
        # Retorna status inicial
        return BatchProcessingResult(
            job_id=job_id,
            total_emails=len(batch.emails),
            processed=0,
            succeeded=0,
            failed=0,
            status=ProcessingStatus.QUEUED,
            results=[],
            started_at=datetime.utcnow()
        )
    
    # Processamento síncrono
    logger.info(f"Processando lote de {len(batch.emails)} e-mails")
    
    results = await gemini_service.process_batch(
        emails=batch.emails,
        system_prompt=system_prompt,
        max_concurrent=settings.MAX_CONCURRENT_REQUESTS
    )
    
    # Conta sucessos e falhas
    succeeded = sum(1 for r in results if r.status == ProcessingStatus.COMPLETED)
    failed = sum(1 for r in results if r.status == ProcessingStatus.FAILED)
    
    return BatchProcessingResult(
        job_id=job_id,
        total_emails=len(batch.emails),
        processed=len(results),
        succeeded=succeeded,
        failed=failed,
        status=ProcessingStatus.COMPLETED,
        results=results,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )


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
    summary="Testar conexão com Gemini",
    description="Verifica se a conexão com Google Gemini está funcionando"
)
async def test_gemini_connection(
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Testa conexão com Gemini API
    """
    try:
        is_connected = await gemini_service.test_connection()
        
        return {
            "connected": is_connected,
            "model": settings.GEMINI_MODEL,
            "message": "Conexão bem-sucedida" if is_connected else "Falha na conexão"
        }
        
    except Exception as e:
        logger.error(f"Erro ao testar conexão: {e}")
        return {
            "connected": False,
            "error": str(e),
            "message": "Erro ao testar conexão com Gemini"
        }


# Função auxiliar para processamento em background
async def _process_batch_background(
    job_id: str,
    emails: List[EmailInput],
    system_prompt: Optional[str],
    webhook_url: Optional[str]
):
    """
    Processa lote em background
    """
    logger.info(f"Iniciando processamento em background do job {job_id}")
    
    try:
        # Processa e-mails
        results = await gemini_service.process_batch(
            emails=emails,
            system_prompt=system_prompt
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