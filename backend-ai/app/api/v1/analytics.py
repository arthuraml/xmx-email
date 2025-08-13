"""
Endpoints para analytics e consulta de dados de processamento
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, date
from loguru import logger

from ...core.security import verify_api_key
from ...db.supabase import get_supabase
from ...services.cost_service import cost_service
from ...services.currency_service import currency_service

# Router para endpoints de analytics
router = APIRouter()


@router.get(
    "/processed",
    summary="Listar e-mails processados com custos",
    description="Retorna lista de e-mails processados com informações de custo"
)
async def get_processed_emails(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    start_date: Optional[str] = Query(default=None, description="Data inicial (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="Data final (YYYY-MM-DD)"),
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Lista e-mails processados com informações detalhadas de custo
    """
    try:
        supabase = get_supabase()
        
        # Constrói query base
        query = supabase.table("processed_emails").select(
            "*",
            count="exact"
        )
        
        # Adiciona filtros de data se fornecidos
        if start_date:
            query = query.gte("created_at", f"{start_date}T00:00:00")
        if end_date:
            query = query.lte("created_at", f"{end_date}T23:59:59")
        
        # Aplica paginação e ordenação
        query = query.order("created_at", desc=True).limit(limit).offset(offset)
        
        # Executa query
        result = query.execute()
        
        # Calcula totais
        emails = result.data
        total_cost_brl = sum(e.get("cost_total_brl", 0) for e in emails)
        total_cost_usd = sum(e.get("cost_total_usd", 0) for e in emails)
        total_tokens = sum(e.get("total_tokens", 0) for e in emails)
        
        return {
            "emails": emails,
            "pagination": {
                "total": result.count,
                "limit": limit,
                "offset": offset,
                "has_more": result.count > (offset + limit)
            },
            "summary": {
                "total_processed": len(emails),
                "total_cost_brl": round(total_cost_brl, 2),
                "total_cost_usd": round(total_cost_usd, 6),
                "total_tokens": total_tokens,
                "avg_cost_per_email_brl": round(total_cost_brl / len(emails), 2) if emails else 0,
                "avg_tokens_per_email": total_tokens // len(emails) if emails else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching processed emails: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching processed emails: {str(e)}"
        )


@router.get(
    "/costs/summary",
    summary="Resumo de custos",
    description="Retorna resumo agregado de custos de processamento"
)
async def get_cost_summary(
    period: str = Query(default="today", regex="^(today|week|month|all)$"),
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Retorna resumo de custos para o período especificado
    """
    try:
        supabase = get_supabase()
        
        # Define período de consulta
        now = datetime.now()
        if period == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_date = now - timedelta(days=7)
        elif period == "month":
            start_date = now - timedelta(days=30)
        else:  # all
            start_date = None
        
        # Query para processed_emails
        query = supabase.table("processed_emails").select(
            "cost_total_brl, cost_total_usd, total_tokens, "
            "prompt_tokens, output_tokens, thought_tokens, "
            "created_at, urgency, email_type"
        )
        
        if start_date:
            query = query.gte("created_at", start_date.isoformat())
        
        processed_result = query.execute()
        
        # Query para llm_responses  
        query = supabase.table("llm_responses").select(
            "cost_total_brl, cost_total_usd, created_at"
        )
        
        if start_date:
            query = query.gte("created_at", start_date.isoformat())
        
        responses_result = query.execute()
        
        # Calcula estatísticas
        processed_emails = processed_result.data
        llm_responses = responses_result.data
        
        # Custos totais de processamento
        processing_cost_brl = sum(e.get("cost_total_brl", 0) for e in processed_emails)
        processing_cost_usd = sum(e.get("cost_total_usd", 0) for e in processed_emails)
        
        # Custos totais de respostas
        response_cost_brl = sum(r.get("cost_total_brl", 0) for r in llm_responses)
        response_cost_usd = sum(r.get("cost_total_usd", 0) for r in llm_responses)
        
        # Tokens totais
        total_input_tokens = sum(e.get("prompt_tokens", 0) for e in processed_emails)
        total_output_tokens = sum(e.get("output_tokens", 0) for e in processed_emails)
        total_thinking_tokens = sum(e.get("thought_tokens", 0) for e in processed_emails)
        
        # Distribuição por tipo
        type_distribution = {}
        for email in processed_emails:
            email_type = email.get("email_type", "other")
            if email_type not in type_distribution:
                type_distribution[email_type] = {
                    "count": 0,
                    "cost_brl": 0,
                    "cost_usd": 0
                }
            type_distribution[email_type]["count"] += 1
            type_distribution[email_type]["cost_brl"] += email.get("cost_total_brl", 0)
            type_distribution[email_type]["cost_usd"] += email.get("cost_total_usd", 0)
        
        # Distribuição por urgência
        urgency_distribution = {}
        for email in processed_emails:
            urgency = email.get("urgency", "medium")
            if urgency not in urgency_distribution:
                urgency_distribution[urgency] = {
                    "count": 0,
                    "cost_brl": 0
                }
            urgency_distribution[urgency]["count"] += 1
            urgency_distribution[urgency]["cost_brl"] += email.get("cost_total_brl", 0)
        
        # Taxa de câmbio atual
        exchange_rate = await currency_service.get_exchange_rate()
        
        return {
            "period": period,
            "period_start": start_date.isoformat() if start_date else None,
            "costs": {
                "processing": {
                    "total_brl": round(processing_cost_brl, 2),
                    "total_usd": round(processing_cost_usd, 6),
                    "count": len(processed_emails)
                },
                "responses": {
                    "total_brl": round(response_cost_brl, 2),
                    "total_usd": round(response_cost_usd, 6),
                    "count": len(llm_responses)
                },
                "combined": {
                    "total_brl": round(processing_cost_brl + response_cost_brl, 2),
                    "total_usd": round(processing_cost_usd + response_cost_usd, 6),
                    "total_operations": len(processed_emails) + len(llm_responses)
                }
            },
            "tokens": {
                "input": total_input_tokens,
                "output": total_output_tokens,
                "thinking": total_thinking_tokens,
                "total": total_input_tokens + total_output_tokens + total_thinking_tokens
            },
            "averages": {
                "cost_per_email_brl": round(processing_cost_brl / len(processed_emails), 2) if processed_emails else 0,
                "cost_per_response_brl": round(response_cost_brl / len(llm_responses), 2) if llm_responses else 0,
                "tokens_per_email": (total_input_tokens + total_output_tokens) // len(processed_emails) if processed_emails else 0
            },
            "distribution": {
                "by_type": type_distribution,
                "by_urgency": urgency_distribution
            },
            "current_exchange_rate": exchange_rate,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating cost summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating cost summary: {str(e)}"
        )


@router.get(
    "/costs/daily",
    summary="Custos diários",
    description="Retorna custos agregados por dia"
)
async def get_daily_costs(
    days: int = Query(default=7, ge=1, le=90),
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Retorna custos agregados por dia para o período especificado
    """
    try:
        supabase = get_supabase()
        
        # Define período
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Busca dados de processed_emails
        query = supabase.table("processed_emails").select(
            "created_at, cost_total_brl, cost_total_usd, total_tokens"
        ).gte("created_at", start_date.isoformat())
        
        result = query.execute()
        
        # Agrupa por dia
        daily_data = {}
        for record in result.data:
            # Extrai data do timestamp
            created_at = datetime.fromisoformat(record["created_at"].replace("Z", "+00:00"))
            day_key = created_at.date().isoformat()
            
            if day_key not in daily_data:
                daily_data[day_key] = {
                    "date": day_key,
                    "cost_brl": 0,
                    "cost_usd": 0,
                    "tokens": 0,
                    "count": 0
                }
            
            daily_data[day_key]["cost_brl"] += record.get("cost_total_brl", 0)
            daily_data[day_key]["cost_usd"] += record.get("cost_total_usd", 0)
            daily_data[day_key]["tokens"] += record.get("total_tokens", 0)
            daily_data[day_key]["count"] += 1
        
        # Converte para lista ordenada
        daily_list = sorted(daily_data.values(), key=lambda x: x["date"])
        
        # Calcula totais
        total_cost_brl = sum(d["cost_brl"] for d in daily_list)
        total_cost_usd = sum(d["cost_usd"] for d in daily_list)
        total_tokens = sum(d["tokens"] for d in daily_list)
        total_count = sum(d["count"] for d in daily_list)
        
        return {
            "period": {
                "start": start_date.date().isoformat(),
                "end": end_date.date().isoformat(),
                "days": days
            },
            "daily": daily_list,
            "totals": {
                "cost_brl": round(total_cost_brl, 2),
                "cost_usd": round(total_cost_usd, 6),
                "tokens": total_tokens,
                "emails": total_count,
                "daily_avg_brl": round(total_cost_brl / len(daily_list), 2) if daily_list else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching daily costs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching daily costs: {str(e)}"
        )


@router.get(
    "/exchange-rate",
    summary="Taxa de câmbio atual",
    description="Retorna a taxa de câmbio USD/BRL atual"
)
async def get_exchange_rate(
    force_refresh: bool = Query(default=False),
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Retorna a taxa de câmbio atual USD/BRL
    """
    try:
        rate = await currency_service.get_exchange_rate(force_refresh=force_refresh)
        cache_info = currency_service.get_cache_info()
        
        return {
            "exchange_rate": rate,
            "currency_pair": "USD/BRL",
            "cache": cache_info,
            "conversion_example": {
                "usd": 1.00,
                "brl": round(rate, 2)
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching exchange rate: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching exchange rate: {str(e)}"
        )


@router.get(
    "/pricing",
    summary="Informações de pricing",
    description="Retorna configuração de preços dos modelos"
)
async def get_pricing_info(
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Retorna informações de pricing dos modelos
    """
    try:
        pricing = cost_service.get_pricing_info()
        exchange_rate = await currency_service.get_exchange_rate()
        
        # Adiciona conversão para BRL
        models_with_brl = {}
        for model_name, model_info in pricing.get("models", {}).items():
            models_with_brl[model_name] = model_info.copy()
            if "costs_usd" in model_info:
                costs_brl = {}
                for token_type, cost_usd in model_info["costs_usd"].items():
                    costs_brl[token_type] = round(cost_usd * exchange_rate, 2)
                models_with_brl[model_name]["costs_brl"] = costs_brl
        
        return {
            "models": models_with_brl,
            "exchange_rate": exchange_rate,
            "last_updated": pricing.get("last_updated"),
            "source": pricing.get("source")
        }
        
    except Exception as e:
        logger.error(f"Error fetching pricing info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching pricing info: {str(e)}"
        )


@router.post(
    "/estimate",
    summary="Estimar custos",
    description="Estima custos para um processamento futuro"
)
async def estimate_costs(
    input_tokens: int,
    output_tokens: int = 0,
    thinking_tokens: int = 0,
    model: str = "gemini-2.5-flash",
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Estima custos para um processamento baseado em tokens estimados
    """
    try:
        from ...models.processing import TokenUsage
        
        token_usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            thought_tokens=thinking_tokens,
            total_tokens=input_tokens + output_tokens + thinking_tokens
        )
        
        estimate = await cost_service.calculate_costs(token_usage, model)
        
        return {
            "estimate": estimate,
            "warning": "This is an estimate. Actual costs may vary based on model usage and thinking tokens."
        }
        
    except Exception as e:
        logger.error(f"Error estimating costs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error estimating costs: {str(e)}"
        )