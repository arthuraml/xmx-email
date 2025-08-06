"""
Modelos Pydantic para geração de respostas
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from .classification import ClassificationType
from .tracking import TrackingData


class ResponseTone(str, Enum):
    """Tom da resposta"""
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    EMPATHETIC = "empathetic"
    FORMAL = "formal"
    INFORMATIVE = "informative"


class ResponseGenerationInput(BaseModel):
    """Entrada para geração de resposta"""
    email_id: str = Field(..., description="ID do e-mail")
    
    # Conteúdo original do e-mail
    email_content: Dict[str, Any] = Field(..., description="Conteúdo completo do e-mail")
    
    # Resultado da classificação
    classification: Dict[str, Any] = Field(..., description="Resultado da classificação")
    
    # Dados de rastreamento (opcional)
    tracking_data: Optional[TrackingData] = Field(None, description="Dados de rastreamento se disponível")
    
    # Opções de personalização
    custom_tone: Optional[ResponseTone] = Field(None, description="Tom customizado para resposta")
    include_signature: bool = Field(True, description="Incluir assinatura padrão")
    priority_message: Optional[str] = Field(None, description="Mensagem prioritária para incluir")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email_id": "msg_12345",
                "email_content": {
                    "from": "cliente@example.com",
                    "to": "support@biofraga.com",
                    "subject": "Produto com defeito e rastreamento",
                    "body": "Meu produto veio com defeito e quero saber onde está minha devolução"
                },
                "classification": {
                    "is_support": True,
                    "is_tracking": True,
                    "urgency": "high"
                },
                "tracking_data": {
                    "order_id": "PED-2025-001",
                    "tracking_code": "BR123456789BR",
                    "status": "EM_TRANSITO"
                }
            }
        }
    }


class GeneratedResponse(BaseModel):
    """Resposta gerada pela LLM"""
    email_id: str = Field(..., description="ID do e-mail")
    
    # Resposta sugerida
    suggested_subject: str = Field(..., description="Assunto sugerido")
    suggested_body: str = Field(..., description="Corpo da resposta")
    tone: ResponseTone = Field(..., description="Tom utilizado")
    
    # Flags de conteúdo
    addresses_support: bool = Field(..., description="Se endereça questões de suporte")
    addresses_tracking: bool = Field(..., description="Se inclui informações de rastreamento")
    
    # Dados incluídos
    tracking_included: Optional[Dict[str, Any]] = Field(None, description="Resumo do rastreamento incluído")
    
    # Ações e acompanhamento
    priority_actions: List[str] = Field(default_factory=list, description="Ações prioritárias para o cliente")
    requires_followup: bool = Field(False, description="Se requer acompanhamento")
    internal_notes: Optional[str] = Field(None, description="Notas internas para a equipe")
    
    # Metadados
    response_type: str = Field(..., description="Tipo de resposta (support/tracking/combined)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confiança na resposta")
    processing_time_ms: int = Field(..., description="Tempo de processamento")
    
    # Tokens
    prompt_tokens: Optional[int] = Field(None, description="Tokens do prompt")
    output_tokens: Optional[int] = Field(None, description="Tokens da resposta")
    total_tokens: Optional[int] = Field(None, description="Total de tokens")
    
    # Status
    saved_to_db: bool = Field(False, description="Se foi salvo no banco")
    error: Optional[str] = Field(None, description="Erro se houver")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email_id": "msg_12345",
                "suggested_subject": "Re: Produto com defeito - Suporte e Rastreamento Biofraga",
                "suggested_body": "Olá! Lamentamos sobre o defeito...",
                "tone": "empathetic",
                "addresses_support": True,
                "addresses_tracking": True,
                "tracking_included": {
                    "code": "BR123456789BR",
                    "status": "EM_TRANSITO",
                    "estimated_delivery": "09/01/2025"
                },
                "priority_actions": ["Enviar fotos do defeito", "Aguardar entrega"],
                "requires_followup": True,
                "response_type": "combined",
                "confidence": 0.95,
                "processing_time_ms": 2500
            }
        }
    }


class BatchResponseGenerationInput(BaseModel):
    """Entrada para geração de respostas em lote"""
    requests: List[ResponseGenerationInput] = Field(..., min_length=1, max_length=10)
    save_to_db: bool = Field(True, description="Salvar respostas no banco")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "requests": [
                    {
                        "email_id": "msg_001",
                        "email_content": {...},
                        "classification": {...}
                    }
                ],
                "save_to_db": True
            }
        }
    }


class BatchResponseGenerationResult(BaseModel):
    """Resultado da geração de respostas em lote"""
    total_requests: int = Field(..., description="Total de requisições")
    successful: int = Field(..., description="Quantidade bem-sucedida")
    failed: int = Field(..., description="Quantidade com falha")
    responses: List[GeneratedResponse] = Field(..., description="Respostas geradas")
    processing_time_ms: int = Field(..., description="Tempo total de processamento")
    
    @property
    def success_rate(self) -> float:
        """Calcula taxa de sucesso"""
        if self.total_requests == 0:
            return 0.0
        return self.successful / self.total_requests