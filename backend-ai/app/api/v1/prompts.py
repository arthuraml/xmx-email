"""
Endpoints para gerenciamento de prompts
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from uuid import uuid4

from ...core.config import settings
from ...core.security import verify_api_key
from ...models.prompt import (
    PromptCreate,
    PromptUpdate,
    PromptResponse,
    PromptList,
    DecisionCriteria
)

router = APIRouter()


@router.get(
    "/current",
    response_model=PromptResponse,
    summary="Obter prompt atual",
    description="Retorna o prompt atualmente ativo"
)
async def get_current_prompt(
    api_key: str = Depends(verify_api_key)
) -> PromptResponse:
    """
    Retorna o prompt padrão (por enquanto)
    """
    return PromptResponse(
        id=uuid4(),
        name="default",
        system_prompt=settings.DEFAULT_SYSTEM_PROMPT,
        decision_criteria=DecisionCriteria(),
        description="Prompt padrão do sistema",
        active=True,
        created_by="system",
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
        usage_count=0
    )


@router.post(
    "/",
    response_model=PromptResponse,
    summary="Criar novo prompt",
    description="Cria um novo prompt no sistema"
)
async def create_prompt(
    prompt: PromptCreate,
    api_key: str = Depends(verify_api_key)
) -> PromptResponse:
    """
    Cria novo prompt (placeholder)
    """
    # TODO: Implementar persistência no Supabase
    raise HTTPException(
        status_code=501,
        detail="Criação de prompts será implementada em breve"
    )


@router.put(
    "/{prompt_id}",
    response_model=PromptResponse,
    summary="Atualizar prompt",
    description="Atualiza um prompt existente"
)
async def update_prompt(
    prompt_id: str,
    prompt_update: PromptUpdate,
    api_key: str = Depends(verify_api_key)
) -> PromptResponse:
    """
    Atualiza prompt (placeholder)
    """
    # TODO: Implementar atualização no Supabase
    raise HTTPException(
        status_code=501,
        detail="Atualização de prompts será implementada em breve"
    )


@router.get(
    "/",
    response_model=PromptList,
    summary="Listar prompts",
    description="Lista todos os prompts cadastrados"
)
async def list_prompts(
    page: int = 1,
    per_page: int = 20,
    api_key: str = Depends(verify_api_key)
) -> PromptList:
    """
    Lista prompts (placeholder)
    """
    # Por enquanto, retorna apenas o prompt padrão
    default_prompt = PromptResponse(
        id=uuid4(),
        name="default",
        system_prompt=settings.DEFAULT_SYSTEM_PROMPT,
        decision_criteria=DecisionCriteria(),
        description="Prompt padrão do sistema",
        active=True,
        created_by="system",
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
        usage_count=0
    )
    
    return PromptList(
        items=[default_prompt],
        total=1,
        page=page,
        per_page=per_page
    )


@router.post(
    "/test",
    summary="Testar prompt",
    description="Testa um prompt com um e-mail de exemplo"
)
async def test_prompt(
    test_request: Dict[str, Any],
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Testa prompt (placeholder)
    """
    # TODO: Implementar teste real com Gemini
    return {
        "message": "Teste de prompt será implementado em breve",
        "test_request": test_request
    }