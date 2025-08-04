"""
Modelos Pydantic para respostas do Gemini e processamento
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, Dict, Any, Literal, List
from enum import Enum

from .email import EmailPriority


class DecisionType(str, Enum):
    """Tipos de decisão possíveis"""
    RESPOND = "respond"
    IGNORE = "ignore"


class EmailType(str, Enum):
    """Classificação do tipo de e-mail"""
    QUESTION = "question"
    COMPLAINT = "complaint"
    REQUEST = "request"
    SPAM = "spam"
    NEWSLETTER = "newsletter"
    AUTO_REPLY = "auto_reply"
    OTHER = "other"


class ResponseTone(str, Enum):
    """Tom da resposta sugerida"""
    FORMAL = "formal"
    INFORMAL = "informal"
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"


class ProcessingStatus(str, Enum):
    """Status do processamento"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SuggestedResponse(BaseModel):
    """Resposta sugerida pelo Gemini"""
    subject: str = Field(..., description="Assunto da resposta", min_length=1)
    body: str = Field(..., description="Corpo da resposta", min_length=10)
    tone: ResponseTone = Field(ResponseTone.PROFESSIONAL, description="Tom da resposta")
    
    @field_validator('body')
    @classmethod
    def validate_body_content(cls, v: str) -> str:
        """Valida conteúdo mínimo no corpo"""
        if len(v.strip()) < 10:
            raise ValueError("O corpo da resposta deve ter pelo menos 10 caracteres")
        return v


class GeminiDecision(BaseModel):
    """Decisão tomada pelo Gemini sobre o e-mail"""
    decision: DecisionType = Field(..., description="Decisão: responder ou ignorar")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Nível de confiança na decisão")
    email_type: EmailType = Field(..., description="Classificação do tipo de e-mail")
    urgency: EmailPriority = Field(..., description="Nível de urgência identificado")
    reason: str = Field(..., description="Explicação da decisão", min_length=10)
    suggested_response: Optional[SuggestedResponse] = Field(
        None, 
        description="Resposta sugerida (apenas se decision=respond)"
    )
    
    @field_validator('suggested_response')
    @classmethod
    def validate_response_consistency(cls, v: Optional[SuggestedResponse], info) -> Optional[SuggestedResponse]:
        """Valida que resposta só existe se decision=respond"""
        if info.data.get('decision') == DecisionType.RESPOND and v is None:
            raise ValueError("Resposta sugerida é obrigatória quando decision=respond")
        elif info.data.get('decision') == DecisionType.IGNORE and v is not None:
            raise ValueError("Resposta sugerida não deve existir quando decision=ignore")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "decision": "respond",
                "confidence": 0.92,
                "email_type": "question",
                "urgency": "medium",
                "reason": "Cliente fazendo pergunta direta sobre funcionalidades do produto",
                "suggested_response": {
                    "subject": "Re: Dúvida sobre produto",
                    "body": "Olá! Obrigado por entrar em contato conosco.\n\nFicamos felizes com seu interesse em nosso produto. [Resposta detalhada aqui]\n\nEstamos à disposição para mais esclarecimentos.\n\nAtenciosamente,\nEquipe Biofraga",
                    "tone": "professional"
                }
            }
        }
    }


class EmailProcessingResult(BaseModel):
    """Resultado do processamento de um e-mail"""
    status: ProcessingStatus = Field(..., description="Status do processamento")
    email_id: str = Field(..., description="ID do e-mail processado")
    decision: Optional[DecisionType] = Field(None, description="Decisão tomada")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confiança na decisão")
    reason: Optional[str] = Field(None, description="Razão da decisão")
    suggested_response: Optional[SuggestedResponse] = Field(None, description="Resposta sugerida")
    processing_time: float = Field(..., ge=0.0, description="Tempo de processamento em segundos")
    processed_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp do processamento")
    job_id: Optional[str] = Field(None, description="ID do job (para processamento assíncrono)")
    error: Optional[str] = Field(None, description="Mensagem de erro se falhou")
    
    # Token usage information
    prompt_tokens: Optional[int] = Field(None, ge=0, description="Número de tokens de entrada (prompt)")
    output_tokens: Optional[int] = Field(None, ge=0, description="Número de tokens de saída (resposta)")
    thought_tokens: Optional[int] = Field(None, ge=0, description="Número de tokens de pensamento (para modelos com thinking)")
    total_tokens: Optional[int] = Field(None, ge=0, description="Total de tokens utilizados")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "completed",
                "email_id": "msg_12345",
                "decision": "respond",
                "confidence": 0.92,
                "reason": "Cliente fazendo pergunta direta sobre produto",
                "suggested_response": {
                    "subject": "Re: Dúvida sobre produto",
                    "body": "Olá! Obrigado por entrar em contato...",
                    "tone": "professional"
                },
                "processing_time": 1.234,
                "processed_at": "2025-01-15T10:30:02Z",
                "prompt_tokens": 250,
                "output_tokens": 180,
                "thought_tokens": 0,
                "total_tokens": 430
            }
        }
    }


class BatchProcessingResult(BaseModel):
    """Resultado do processamento em lote"""
    job_id: str = Field(..., description="ID do job de processamento")
    total_emails: int = Field(..., ge=1, description="Total de e-mails no lote")
    processed: int = Field(0, ge=0, description="Quantidade processada")
    succeeded: int = Field(0, ge=0, description="Quantidade com sucesso")
    failed: int = Field(0, ge=0, description="Quantidade com falha")
    status: ProcessingStatus = Field(..., description="Status geral do lote")
    results: List[EmailProcessingResult] = Field(default_factory=list, description="Resultados individuais")
    started_at: datetime = Field(..., description="Início do processamento")
    completed_at: Optional[datetime] = Field(None, description="Fim do processamento")
    
    @property
    def success_rate(self) -> float:
        """Calcula taxa de sucesso"""
        if self.processed == 0:
            return 0.0
        return self.succeeded / self.processed
    
    @property
    def is_complete(self) -> bool:
        """Verifica se o processamento está completo"""
        return self.processed == self.total_emails


class EmailStatusResponse(BaseModel):
    """Resposta para consulta de status de e-mail"""
    email_id: str
    status: ProcessingStatus
    decision: Optional[DecisionType] = None
    processed_at: Optional[datetime] = None
    response_sent: bool = False
    response_details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None