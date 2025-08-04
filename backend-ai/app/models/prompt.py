"""
Modelos Pydantic para gerenciamento de prompts do sistema
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, Dict, List, Any
from uuid import UUID, uuid4


class DecisionCriteria(BaseModel):
    """Critérios para tomada de decisão"""
    respond_to: List[str] = Field(
        default_factory=lambda: ["questions", "complaints", "requests", "urgent"],
        description="Tipos de e-mail que devem ser respondidos"
    )
    ignore: List[str] = Field(
        default_factory=lambda: ["spam", "newsletters", "auto_replies"],
        description="Tipos de e-mail que devem ser ignorados"
    )
    custom_rules: Dict[str, Any] = Field(
        default_factory=dict,
        description="Regras customizadas adicionais"
    )


class PromptCreate(BaseModel):
    """Modelo para criação de novo prompt"""
    name: str = Field(..., description="Nome único do prompt", min_length=3, max_length=255)
    system_prompt: str = Field(..., description="Conteúdo do system prompt", min_length=50)
    decision_criteria: DecisionCriteria = Field(
        default_factory=DecisionCriteria,
        description="Critérios de decisão"
    )
    description: Optional[str] = Field(None, description="Descrição do prompt", max_length=500)
    active: bool = Field(False, description="Se este prompt está ativo")
    
    @field_validator('name')
    @classmethod
    def validate_name_format(cls, v: str) -> str:
        """Valida formato do nome (apenas letras, números, - e _)"""
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Nome deve conter apenas letras, números, hífens e underscores")
        return v.lower()
    
    @field_validator('system_prompt')
    @classmethod
    def validate_prompt_content(cls, v: str) -> str:
        """Valida conteúdo mínimo do prompt"""
        if len(v.strip()) < 50:
            raise ValueError("System prompt deve ter pelo menos 50 caracteres")
        return v


class PromptUpdate(BaseModel):
    """Modelo para atualização de prompt"""
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    system_prompt: Optional[str] = Field(None, min_length=50)
    decision_criteria: Optional[DecisionCriteria] = None
    description: Optional[str] = Field(None, max_length=500)
    active: Optional[bool] = None


class PromptResponse(BaseModel):
    """Modelo de resposta para prompts"""
    id: UUID = Field(default_factory=uuid4, description="ID único do prompt")
    name: str = Field(..., description="Nome do prompt")
    system_prompt: str = Field(..., description="Conteúdo do system prompt")
    decision_criteria: DecisionCriteria = Field(..., description="Critérios de decisão")
    description: Optional[str] = Field(None, description="Descrição do prompt")
    active: bool = Field(..., description="Se o prompt está ativo")
    created_by: Optional[str] = Field(None, description="Usuário que criou")
    created_at: datetime = Field(..., description="Data de criação")
    updated_at: datetime = Field(..., description="Data de última atualização")
    usage_count: int = Field(0, description="Quantidade de vezes usado")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "default",
                "system_prompt": "Você é um assistente inteligente de e-mail...",
                "decision_criteria": {
                    "respond_to": ["questions", "complaints", "urgent"],
                    "ignore": ["spam", "newsletters"],
                    "custom_rules": {
                        "min_confidence": 0.7,
                        "auto_reply_delay": 300
                    }
                },
                "description": "Prompt padrão para processamento de e-mails",
                "active": True,
                "created_by": "admin@biofraga.com",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-15T10:30:00Z",
                "usage_count": 1523
            }
        }
    }


class PromptList(BaseModel):
    """Lista paginada de prompts"""
    items: List[PromptResponse] = Field(..., description="Lista de prompts")
    total: int = Field(..., ge=0, description="Total de prompts")
    page: int = Field(1, ge=1, description="Página atual")
    per_page: int = Field(20, ge=1, le=100, description="Itens por página")
    
    @property
    def total_pages(self) -> int:
        """Calcula total de páginas"""
        return (self.total + self.per_page - 1) // self.per_page
    
    @property
    def has_next(self) -> bool:
        """Verifica se há próxima página"""
        return self.page < self.total_pages
    
    @property
    def has_prev(self) -> bool:
        """Verifica se há página anterior"""
        return self.page > 1


class PromptTestRequest(BaseModel):
    """Requisição para testar um prompt com um e-mail"""
    prompt_id: UUID = Field(..., description="ID do prompt a testar")
    email_sample: Dict[str, Any] = Field(..., description="Amostra de e-mail para teste")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "prompt_id": "550e8400-e29b-41d4-a716-446655440000",
                "email_sample": {
                    "from": "teste@example.com",
                    "to": "support@biofraga.com",
                    "subject": "Teste de prompt",
                    "body": "Este é um e-mail de teste para verificar o prompt"
                }
            }
        }
    }


class PromptTestResponse(BaseModel):
    """Resposta do teste de prompt"""
    prompt_id: UUID
    test_result: Dict[str, Any] = Field(..., description="Resultado do teste")
    execution_time: float = Field(..., description="Tempo de execução em segundos")
    tokens_used: int = Field(..., description="Tokens utilizados")
    success: bool = Field(..., description="Se o teste foi bem-sucedido")