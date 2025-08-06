"""
Endpoints para geração de respostas de e-mail
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
from loguru import logger

from ...core.security import verify_api_key
from ...models.response_generation import (
    ResponseGenerationInput,
    GeneratedResponse,
    BatchResponseGenerationInput,
    BatchResponseGenerationResult,
    ResponseTone
)
from ...services.response_service import response_service

# Router para endpoints de geração de resposta
router = APIRouter()


@router.post(
    "/generate",
    response_model=GeneratedResponse,
    summary="Gerar resposta para e-mail",
    description="Gera resposta usando LLM com base na classificação e dados de rastreamento"
)
async def generate_response(
    request: ResponseGenerationInput,
    save_to_db: bool = True,
    api_key: str = Depends(verify_api_key)
) -> GeneratedResponse:
    """
    Gera resposta para e-mail usando Gemini AI
    
    Este é o endpoint final que recebe:
    - Conteúdo original do e-mail
    - Resultado da classificação (is_support, is_tracking)
    - Dados de rastreamento (se disponível)
    
    E gera uma resposta apropriada usando o prompt correto:
    - support_response_prompt.txt para apenas suporte
    - combined_response_prompt.txt para suporte + rastreamento
    
    Args:
        request: Dados completos para geração da resposta
        save_to_db: Se deve salvar no banco (padrão: True)
    
    Returns:
        Resposta gerada com sugestão de assunto e corpo
    """
    try:
        logger.info(
            f"Generating response for email {request.email_id} - "
            f"Support: {request.classification.get('is_support')}, "
            f"Tracking: {request.classification.get('is_tracking')}"
        )
        
        # Gera resposta com Gemini
        result = await response_service.generate_response(
            request=request,
            save_to_db=save_to_db
        )
        
        logger.info(
            f"Response generated for email {request.email_id} - "
            f"Type: {result.response_type}, "
            f"Confidence: {result.confidence:.2f}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar resposta: {str(e)}"
        )


@router.post(
    "/generate-batch",
    response_model=BatchResponseGenerationResult,
    summary="Gerar múltiplas respostas",
    description="Gera respostas para múltiplos e-mails em lote"
)
async def generate_response_batch(
    batch: BatchResponseGenerationInput,
    api_key: str = Depends(verify_api_key)
) -> BatchResponseGenerationResult:
    """
    Gera respostas para múltiplos e-mails em lote
    
    Args:
        batch: Lote de requisições para gerar respostas
    
    Returns:
        Resultado da geração em lote
    """
    try:
        logger.info(f"Generating batch responses for {len(batch.requests)} emails")
        
        result = await response_service.generate_batch(
            requests=batch.requests,
            save_to_db=batch.save_to_db
        )
        
        logger.info(
            f"Batch generation completed - "
            f"Success: {result.successful}/{result.total_requests}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in batch generation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro na geração em lote: {str(e)}"
        )


@router.get(
    "/test",
    summary="Testar serviço de geração",
    description="Testa o serviço de geração de respostas"
)
async def test_response_service(
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Testa o serviço de geração de respostas
    """
    try:
        # Cria requisição de teste
        test_request = ResponseGenerationInput(
            email_id="test_001",
            email_content={
                "from": "teste@example.com",
                "to": "support@biofraga.com",
                "subject": "Teste de geração",
                "body": "Este é um teste do serviço de geração de respostas."
            },
            classification={
                "is_support": True,
                "is_tracking": False,
                "urgency": "low",
                "email_type": "question"
            },
            tracking_data=None
        )
        
        result = await response_service.generate_response(
            request=test_request,
            save_to_db=False  # Não salva teste no banco
        )
        
        return {
            "status": "ok",
            "message": "Serviço de geração funcionando",
            "test_result": {
                "subject": result.suggested_subject[:50] + "...",
                "tone": result.tone.value,
                "response_type": result.response_type,
                "confidence": result.confidence
            }
        }
        
    except Exception as e:
        logger.error(f"Response service test failed: {e}")
        return {
            "status": "error",
            "message": "Erro no serviço de geração",
            "error": str(e)
        }


@router.post(
    "/preview",
    response_model=GeneratedResponse,
    summary="Preview de resposta",
    description="Gera preview de resposta sem salvar no banco"
)
async def preview_response(
    request: ResponseGenerationInput,
    api_key: str = Depends(verify_api_key)
) -> GeneratedResponse:
    """
    Gera preview de resposta sem salvar no banco
    
    Útil para testar diferentes configurações ou tons
    
    Args:
        request: Dados para geração da resposta
    
    Returns:
        Preview da resposta gerada
    """
    try:
        logger.info(f"Generating preview for email {request.email_id}")
        
        # Sempre gera preview sem salvar
        result = await response_service.generate_response(
            request=request,
            save_to_db=False
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating preview: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar preview: {str(e)}"
        )