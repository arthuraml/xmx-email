"""
Modelos Pydantic para e-mails
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class EmailPriority(str, Enum):
    """Níveis de prioridade do e-mail"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NORMAL = "normal"


class EmailMetadata(BaseModel):
    """Metadados adicionais do e-mail"""
    priority: EmailPriority = EmailPriority.NORMAL
    labels: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class EmailInput(BaseModel):
    """Modelo de entrada para processamento de e-mail"""
    email_id: str = Field(..., description="ID único do e-mail", min_length=1)
    from_address: EmailStr = Field(..., alias="from", description="Endereço de e-mail do remetente")
    to_address: EmailStr = Field(..., alias="to", description="Endereço de e-mail do destinatário")
    subject: str = Field(..., description="Assunto do e-mail", min_length=1)
    body: str = Field(..., description="Corpo do e-mail", min_length=1)
    thread_id: Optional[str] = Field(None, description="ID da thread de conversa")
    received_at: datetime = Field(..., description="Data/hora de recebimento")
    attachments: List[str] = Field(default_factory=list, description="Lista de nomes de anexos")
    metadata: EmailMetadata = Field(default_factory=EmailMetadata, description="Metadados adicionais")
    
    @field_validator('body')
    @classmethod
    def validate_body_not_empty(cls, v: str) -> str:
        """Valida que o corpo do e-mail não está vazio após strip"""
        if not v.strip():
            raise ValueError("O corpo do e-mail não pode estar vazio")
        return v
    
    @field_validator('subject')
    @classmethod
    def validate_subject_not_empty(cls, v: str) -> str:
        """Valida que o assunto não está vazio após strip"""
        if not v.strip():
            raise ValueError("O assunto do e-mail não pode estar vazio")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email_id": "msg_12345",
                "from": "cliente@example.com",
                "to": "support@biofraga.com",
                "subject": "Dúvida sobre produto",
                "body": "Olá, gostaria de saber mais informações sobre o produto X...",
                "thread_id": "thread_123",
                "received_at": "2025-01-15T10:30:00Z",
                "attachments": ["documento.pdf", "imagem.png"],
                "metadata": {
                    "priority": "normal",
                    "labels": ["INBOX", "UNREAD"],
                    "custom_fields": {
                        "department": "sales",
                        "customer_id": "cust_456"
                    }
                }
            }
        },
        "populate_by_name": True  # Permite usar 'from' e 'to' como nomes de campo
    }


class EmailSummary(BaseModel):
    """Resumo de e-mail para listagem"""
    email_id: str
    from_address: str = Field(..., alias="from")
    to_address: str = Field(..., alias="to")
    subject: str
    snippet: str = Field(..., description="Prévia do conteúdo", max_length=200)
    received_at: datetime
    thread_id: Optional[str] = None
    has_attachments: bool = False
    is_processed: bool = False
    decision: Optional[str] = None
    
    model_config = {
        "populate_by_name": True
    }


class EmailBatch(BaseModel):
    """Modelo para processamento em lote de e-mails"""
    emails: List[EmailInput] = Field(..., min_length=1, max_length=100)
    process_async: bool = Field(False, description="Processar de forma assíncrona")
    webhook_url: Optional[str] = Field(None, description="URL para callback quando concluído")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "emails": [
                    {
                        "email_id": "msg_001",
                        "from": "cliente1@example.com",
                        "to": "support@biofraga.com",
                        "subject": "Pergunta 1",
                        "body": "Conteúdo da pergunta 1",
                        "received_at": "2025-01-15T10:00:00Z"
                    },
                    {
                        "email_id": "msg_002",
                        "from": "cliente2@example.com",
                        "to": "support@biofraga.com",
                        "subject": "Pergunta 2",
                        "body": "Conteúdo da pergunta 2",
                        "received_at": "2025-01-15T10:30:00Z"
                    }
                ],
                "process_async": True,
                "webhook_url": "https://example.com/webhook/email-processed"
            }
        }
    }