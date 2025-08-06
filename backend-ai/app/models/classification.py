"""
Modelos Pydantic para classificação de e-mails
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class ClassificationType(str, Enum):
    """Tipos de classificação"""
    SUPPORT = "support"
    TRACKING = "tracking"
    BOTH = "both"
    NONE = "none"


class EmailClassificationInput(BaseModel):
    """Entrada para classificação de e-mail"""
    email_id: str = Field(..., description="ID único do e-mail")
    from_address: EmailStr = Field(..., description="E-mail do remetente")
    to_address: EmailStr = Field(..., description="E-mail do destinatário")
    subject: str = Field(..., description="Assunto do e-mail")
    body: str = Field(..., description="Corpo do e-mail")
    received_at: datetime = Field(..., description="Data/hora de recebimento")
    thread_id: Optional[str] = Field(None, description="ID da thread")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email_id": "msg_12345",
                "from_address": "cliente@example.com",
                "to_address": "support@biofraga.com",
                "subject": "Onde está meu pedido?",
                "body": "Olá, gostaria de saber o status da minha entrega...",
                "received_at": "2025-01-06T10:30:00Z",
                "thread_id": "thread_123"
            }
        }
    }


class EmailClassificationResult(BaseModel):
    """Resultado da classificação de e-mail"""
    email_id: str = Field(..., description="ID do e-mail classificado")
    is_support: bool = Field(..., description="É solicitação de suporte")
    is_tracking: bool = Field(..., description="É solicitação de rastreamento")
    classification_type: ClassificationType = Field(..., description="Tipo combinado")
    sender_email: EmailStr = Field(..., description="E-mail do remetente extraído")
    email_type: str = Field(..., description="Tipo específico do e-mail")
    urgency: str = Field(..., description="Nível de urgência")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confiança na classificação")
    reason: str = Field(..., description="Razão da classificação")
    key_phrases: List[str] = Field(default_factory=list, description="Frases-chave identificadas")
    
    # Metadados de processamento
    processing_time_ms: Optional[int] = Field(None, description="Tempo de processamento")
    prompt_tokens: Optional[int] = Field(None, description="Tokens do prompt")
    output_tokens: Optional[int] = Field(None, description="Tokens da resposta")
    total_tokens: Optional[int] = Field(None, description="Total de tokens")
    
    # Status
    saved_to_db: bool = Field(False, description="Se foi salvo no banco")
    error: Optional[str] = Field(None, description="Erro se houver")
    
    @field_validator('classification_type', mode='before')
    @classmethod
    def determine_classification_type(cls, v, info):
        """Determina o tipo de classificação baseado nos flags"""
        if v is not None:
            return v
            
        data = info.data
        is_support = data.get('is_support', False)
        is_tracking = data.get('is_tracking', False)
        
        if is_support and is_tracking:
            return ClassificationType.BOTH
        elif is_support:
            return ClassificationType.SUPPORT
        elif is_tracking:
            return ClassificationType.TRACKING
        else:
            return ClassificationType.NONE
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email_id": "msg_12345",
                "is_support": False,
                "is_tracking": True,
                "classification_type": "tracking",
                "sender_email": "cliente@example.com",
                "email_type": "tracking",
                "urgency": "medium",
                "confidence": 0.95,
                "reason": "Cliente solicitando informações sobre entrega",
                "key_phrases": ["onde está meu pedido", "status da entrega"],
                "processing_time_ms": 1234,
                "prompt_tokens": 250,
                "output_tokens": 150,
                "total_tokens": 400,
                "saved_to_db": True
            }
        }
    }


class BatchClassificationInput(BaseModel):
    """Entrada para classificação em lote"""
    emails: List[EmailClassificationInput] = Field(..., min_length=1, max_length=50)
    save_to_db: bool = Field(True, description="Salvar resultados no banco")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "emails": [
                    {
                        "email_id": "msg_001",
                        "from_address": "cliente1@example.com",
                        "to_address": "support@biofraga.com",
                        "subject": "Problema com produto",
                        "body": "O produto veio com defeito",
                        "received_at": "2025-01-06T10:00:00Z"
                    }
                ],
                "save_to_db": True
            }
        }
    }


class BatchClassificationResult(BaseModel):
    """Resultado da classificação em lote"""
    total_emails: int = Field(..., description="Total de e-mails processados")
    successful: int = Field(..., description="Quantidade processada com sucesso")
    failed: int = Field(..., description="Quantidade com falha")
    results: List[EmailClassificationResult] = Field(..., description="Resultados individuais")
    processing_time_ms: int = Field(..., description="Tempo total de processamento")
    
    @property
    def success_rate(self) -> float:
        """Calcula taxa de sucesso"""
        if self.total_emails == 0:
            return 0.0
        return self.successful / self.total_emails