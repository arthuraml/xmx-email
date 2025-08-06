"""
Endpoints para classificação de e-mails
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from loguru import logger

from ...core.security import verify_api_key
from ...models.classification import (
    EmailClassificationInput,
    EmailClassificationResult,
    BatchClassificationInput,
    BatchClassificationResult
)
from ...services.classification_service import classification_service

# Router para endpoints de classificação
router = APIRouter()


@router.post(
    "/classify",
    response_model=EmailClassificationResult,
    summary="Classificar um e-mail",
    description="Classifica se o e-mail é suporte e/ou rastreamento"
)
async def classify_email(
    email: EmailClassificationInput,
    save_to_db: bool = True,
    api_key: str = Depends(verify_api_key)
) -> EmailClassificationResult:
    """
    Classifica um e-mail usando Gemini AI
    
    Determina:
    - Se é solicitação de suporte (is_support)
    - Se é solicitação de rastreamento (is_tracking)
    - Extrai e-mail do remetente
    - Avalia urgência e tipo
    
    Args:
        email: Dados do e-mail para classificar
        save_to_db: Se deve salvar no banco (padrão: True)
    
    Returns:
        Resultado da classificação com flags e metadados
    """
    try:
        logger.info(f"Classifying email {email.email_id} from {email.from_address}")
        
        # Classifica com Gemini
        result = await classification_service.classify_email(
            email=email,
            save_to_db=save_to_db
        )
        
        logger.info(
            f"Email {email.email_id} classified - "
            f"Type: {result.classification_type.value}, "
            f"Support: {result.is_support}, "
            f"Tracking: {result.is_tracking}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error classifying email: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao classificar e-mail: {str(e)}"
        )


@router.post(
    "/classify-batch",
    response_model=BatchClassificationResult,
    summary="Classificar múltiplos e-mails",
    description="Classifica um lote de e-mails"
)
async def classify_email_batch(
    batch: BatchClassificationInput,
    api_key: str = Depends(verify_api_key)
) -> BatchClassificationResult:
    """
    Classifica múltiplos e-mails em lote
    
    Args:
        batch: Lote de e-mails para classificar
    
    Returns:
        Resultado da classificação em lote
    """
    try:
        logger.info(f"Classifying batch of {len(batch.emails)} emails")
        
        result = await classification_service.classify_batch(
            emails=batch.emails,
            save_to_db=batch.save_to_db
        )
        
        logger.info(
            f"Batch classification completed - "
            f"Success: {result.successful}/{result.total_emails}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in batch classification: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro na classificação em lote: {str(e)}"
        )


@router.get(
    "/test",
    summary="Testar serviço de classificação",
    description="Verifica se o serviço está funcionando"
)
async def test_classification_service(
    api_key: str = Depends(verify_api_key)
):
    """
    Testa o serviço de classificação
    """
    try:
        # Testa com e-mail de exemplo
        test_email = EmailClassificationInput(
            email_id="test_001",
            from_address="teste@example.com",
            to_address="support@biofraga.com",
            subject="Teste de classificação",
            body="Este é um teste para verificar se o serviço está funcionando.",
            received_at="2025-01-06T12:00:00Z"
        )
        
        result = await classification_service.classify_email(
            email=test_email,
            save_to_db=False  # Não salva teste no banco
        )
        
        return {
            "status": "ok",
            "message": "Serviço de classificação funcionando",
            "test_result": {
                "is_support": result.is_support,
                "is_tracking": result.is_tracking,
                "classification_type": result.classification_type.value,
                "confidence": result.confidence
            }
        }
        
    except Exception as e:
        logger.error(f"Classification service test failed: {e}")
        return {
            "status": "error",
            "message": "Erro no serviço de classificação",
            "error": str(e)
        }