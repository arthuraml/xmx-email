"""
Modelos unificados para processamento de e-mails
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class EmailClassification(BaseModel):
    """Resultado da classificação do e-mail"""
    is_support: bool = Field(..., description="Se é uma solicitação de suporte")
    is_tracking: bool = Field(..., description="Se é uma solicitação de rastreamento")
    urgency: str = Field("medium", description="Nível de urgência: low, medium, high")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confiança na classificação")
    email_type: str = Field("question", description="Tipo do e-mail")
    extracted_order_id: Optional[str] = Field(None, description="ID do pedido extraído do e-mail se mencionado")
    product_name: Optional[str] = Field(None, description="Nome do produto relacionado ao e-mail")


class TrackingInfo(BaseModel):
    """Informações de rastreamento encontradas"""
    order_id: str = Field(..., description="ID do pedido")
    tracking_code: str = Field(..., description="Código de rastreamento")
    purchase_date: datetime = Field(..., description="Data da compra")
    status: Optional[str] = Field(None, description="Status do pedido")


class TrackingResult(BaseModel):
    """Resultado da busca de rastreamento"""
    found: bool = Field(..., description="Se foram encontrados dados de rastreamento")
    orders: List[TrackingInfo] = Field(default_factory=list, description="Lista de pedidos encontrados")
    query_time_ms: int = Field(0, description="Tempo de consulta em ms")
    error: Optional[str] = Field(None, description="Erro se houver")


class TokenUsage(BaseModel):
    """Informações sobre uso de tokens"""
    input_tokens: int = Field(0, ge=0, description="Tokens de entrada")
    output_tokens: int = Field(0, ge=0, description="Tokens de saída")
    thought_tokens: int = Field(0, ge=0, description="Tokens de pensamento")
    total_tokens: int = Field(0, ge=0, description="Total de tokens")


class EmailProcessingResponse(BaseModel):
    """Resposta unificada do processamento de e-mail"""
    email_id: str = Field(..., description="ID do e-mail processado")
    
    # Resultado da classificação
    classification: EmailClassification = Field(..., description="Classificação do e-mail")
    
    # Dados de rastreamento (se aplicável)
    tracking_data: Optional[TrackingResult] = Field(None, description="Dados de rastreamento encontrados")
    
    # Informações de uso
    tokens: TokenUsage = Field(default_factory=TokenUsage, description="Uso de tokens")
    processing_time: float = Field(..., ge=0.0, description="Tempo total de processamento em segundos")
    processed_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp do processamento")
    
    # Mensagem de erro se houver
    error: Optional[str] = Field(None, description="Mensagem de erro se o processamento falhou")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email_id": "msg_123",
                "classification": {
                    "is_support": True,
                    "is_tracking": True,
                    "urgency": "medium",
                    "confidence": 0.92,
                    "email_type": "question",
                    "extracted_order_id": "38495799"
                },
                "tracking_data": {
                    "found": True,
                    "orders": [
                        {
                            "order_id": "38495799",
                            "tracking_code": "9400150899561052495864",
                            "purchase_date": "2025-08-08T11:27:00",
                            "status": "shipped"
                        }
                    ],
                    "query_time_ms": 45
                },
                "tokens": {
                    "input_tokens": 250,
                    "output_tokens": 180,
                    "thought_tokens": 50,
                    "total_tokens": 480
                },
                "processing_time": 1.234,
                "processed_at": "2025-01-15T10:30:02Z"
            }
        }
    }