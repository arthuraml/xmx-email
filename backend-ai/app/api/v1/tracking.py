"""
Endpoints para busca de dados de rastreamento
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
from loguru import logger

from ...core.security import verify_api_key
from ...models.tracking import (
    TrackingQueryInput,
    TrackingQueryResult,
    TrackingData,
    BatchTrackingQueryInput,
    BatchTrackingQueryResult
)
from ...services.mysql_service import mysql_service
from ...db.supabase import get_supabase

# Router para endpoints de rastreamento
router = APIRouter()


@router.post(
    "/query",
    response_model=TrackingQueryResult,
    summary="Buscar dados de rastreamento",
    description="Busca dados de rastreamento no MySQL usando e-mail do cliente"
)
async def query_tracking(
    query: TrackingQueryInput,
    save_to_db: bool = True,
    api_key: str = Depends(verify_api_key)
) -> TrackingQueryResult:
    """
    Busca dados de rastreamento de forma programática no MySQL
    
    NÃO USA LLM - Busca direta no banco de dados
    
    Args:
        query: Dados para busca (email_id, sender_email, order_id opcional)
        save_to_db: Se deve salvar resultado no Supabase
    
    Returns:
        Resultado da busca com dados de rastreamento se encontrado
    """
    try:
        logger.info(
            f"Querying tracking for email {query.email_id} - "
            f"Sender: {query.sender_email}"
        )
        
        # Busca no MySQL
        result = await mysql_service.query_tracking(
            email_id=query.email_id,
            sender_email=query.sender_email,
            order_id=query.order_id
        )
        
        # Salva no Supabase se solicitado e encontrado
        if save_to_db and result.found:
            await _save_tracking_to_supabase(result)
            result.saved_to_db = True
        
        logger.info(
            f"Tracking query for {query.sender_email} - "
            f"Found: {result.found}, "
            f"Source: {result.data_source}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error querying tracking: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar rastreamento: {str(e)}"
        )


@router.post(
    "/query-batch",
    response_model=BatchTrackingQueryResult,
    summary="Buscar múltiplos rastreamentos",
    description="Busca dados de rastreamento para múltiplos e-mails"
)
async def query_tracking_batch(
    batch: BatchTrackingQueryInput,
    api_key: str = Depends(verify_api_key)
) -> BatchTrackingQueryResult:
    """
    Busca múltiplos rastreamentos em lote
    
    Args:
        batch: Lote de consultas
    
    Returns:
        Resultado das buscas em lote
    """
    import asyncio
    import time
    
    start_time = time.time()
    
    try:
        logger.info(f"Batch tracking query for {len(batch.queries)} items")
        
        # Processa consultas em paralelo
        tasks = [
            mysql_service.query_tracking(
                email_id=query.email_id,
                sender_email=query.sender_email,
                order_id=query.order_id
            )
            for query in batch.queries
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processa resultados
        valid_results = []
        found_count = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch query error for item {i}: {result}")
                # Cria resultado de erro
                valid_results.append(
                    TrackingQueryResult(
                        email_id=batch.queries[i].email_id,
                        found=False,
                        query_time_ms=0,
                        data_source="mysql",
                        error=str(result),
                        saved_to_db=False
                    )
                )
            else:
                valid_results.append(result)
                if result.found:
                    found_count += 1
                    
                    # Salva no Supabase se solicitado
                    if batch.save_to_db:
                        await _save_tracking_to_supabase(result)
                        result.saved_to_db = True
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return BatchTrackingQueryResult(
            total_queries=len(batch.queries),
            found_count=found_count,
            not_found_count=len(batch.queries) - found_count,
            results=valid_results,
            processing_time_ms=processing_time_ms
        )
        
    except Exception as e:
        logger.error(f"Error in batch tracking query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro na busca em lote: {str(e)}"
        )


@router.get(
    "/test-connection",
    summary="Testar conexão MySQL",
    description="Verifica se a conexão com MySQL está funcionando"
)
async def test_mysql_connection(
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Testa conexão com MySQL
    """
    try:
        is_connected = await mysql_service.test_connection()
        
        return {
            "connected": is_connected,
            "message": "Conexão MySQL funcionando" if is_connected else "Falha na conexão MySQL"
        }
        
    except Exception as e:
        logger.error(f"MySQL connection test failed: {e}")
        return {
            "connected": False,
            "error": str(e),
            "message": "Erro ao testar conexão MySQL"
        }


@router.post(
    "/insert-sample",
    summary="Inserir dados de exemplo",
    description="Insere dados de rastreamento de exemplo para testes"
)
async def insert_sample_tracking(
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Insere dados de exemplo no MySQL para testes
    """
    try:
        # Dados de exemplo
        sample_data = {
            "customer_email": "teste@example.com",
            "order_id": "PED-2025-TEST",
            "tracking_code": "BR123456789BR",
            "carrier": "Correios",
            "status": "EM_TRANSITO",
            "last_location": "São Paulo/SP",
            "last_update": "2025-01-06T14:30:00",
            "estimated_delivery": "2025-01-09T18:00:00",
            "recipient_name": "Cliente Teste",
            "delivery_address": "Rua Exemplo, 123 - São Paulo/SP",
            "history": [
                {
                    "date": "2025-01-04T10:00:00",
                    "status": "Postado",
                    "location": "São Paulo/SP",
                    "description": "Objeto postado"
                },
                {
                    "date": "2025-01-05T14:00:00",
                    "status": "Em trânsito",
                    "location": "Curitiba/PR",
                    "description": "Objeto em trânsito"
                },
                {
                    "date": "2025-01-06T14:30:00",
                    "status": "Em trânsito",
                    "location": "São Paulo/SP",
                    "description": "Objeto chegou na cidade de destino"
                }
            ]
        }
        
        success = await mysql_service.insert_tracking_data(sample_data)
        
        if success:
            return {
                "success": True,
                "message": "Dados de exemplo inseridos com sucesso",
                "order_id": sample_data["order_id"],
                "customer_email": sample_data["customer_email"]
            }
        else:
            return {
                "success": False,
                "message": "Falha ao inserir dados de exemplo"
            }
            
    except Exception as e:
        logger.error(f"Error inserting sample data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao inserir dados de exemplo: {str(e)}"
        )


async def _save_tracking_to_supabase(result: TrackingQueryResult):
    """
    Salva resultado de rastreamento no Supabase
    
    Args:
        result: Resultado da consulta de rastreamento
    """
    try:
        supabase = get_supabase()
        
        # Prepara dados para inserção
        data = {
            "email_id": result.email_id,
            "sender_email": result.tracking_data.order_id if result.tracking_data else None,
            "order_id": result.tracking_data.order_id if result.tracking_data else None,
            "tracking_code": result.tracking_data.tracking_code if result.tracking_data else None,
            "carrier": result.tracking_data.carrier.value if result.tracking_data else None,
            "status": result.tracking_data.status.value if result.tracking_data else None,
            "last_update": result.tracking_data.last_update.isoformat() if result.tracking_data else None,
            "tracking_details": {
                "last_location": result.tracking_data.last_location if result.tracking_data else None,
                "estimated_delivery": result.tracking_data.estimated_delivery.isoformat() if result.tracking_data and result.tracking_data.estimated_delivery else None,
                "history": [
                    {
                        "date": item.date.isoformat(),
                        "status": item.status,
                        "location": item.location,
                        "description": item.description
                    }
                    for item in (result.tracking_data.history if result.tracking_data else [])
                ]
            },
            "mysql_queried": True,
            "query_success": result.found
        }
        
        # Insere ou atualiza
        response = supabase.table("tracking_requests").upsert(
            data,
            on_conflict="email_id"
        ).execute()
        
        logger.info(f"Tracking data saved to Supabase for email {result.email_id}")
        
    except Exception as e:
        logger.error(f"Failed to save tracking to Supabase: {e}")
        # Não lança exceção para não interromper o fluxo