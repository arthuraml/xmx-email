"""
Configuração e cliente do Google Gemini
"""

from google import genai
from google.genai import types
from typing import Optional, Dict, Any
import json
import os
from loguru import logger

from .config import settings

# Cliente global do Gemini
gemini_client: Optional[genai.Client] = None


def init_gemini_client() -> genai.Client:
    """
    Inicializa o cliente do Google Gemini
    """
    global gemini_client
    
    try:
        gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        logger.info(f"Cliente Gemini inicializado com modelo: {settings.GEMINI_MODEL}")
        return gemini_client
    except Exception as e:
        logger.error(f"Erro ao inicializar cliente Gemini: {e}")
        raise


def get_gemini_client() -> genai.Client:
    """
    Retorna o cliente Gemini ou inicializa se necessário
    """
    global gemini_client
    if gemini_client is None:
        return init_gemini_client()
    return gemini_client


async def analyze_email_with_gemini(
    email_data: Dict[str, Any],
    system_prompt: str,
    model: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analisa um e-mail usando o Google Gemini
    
    Args:
        email_data: Dados do e-mail para análise
        system_prompt: System prompt para o modelo
        model: Modelo específico (opcional, usa padrão se não fornecido)
    
    Returns:
        Dict com a decisão do Gemini
    """
    client = get_gemini_client()
    
    # Prepara o prompt do usuário
    user_prompt = f"""
    Analise o seguinte e-mail:
    
    De: {email_data.get('from_address', 'Desconhecido')}
    Para: {email_data.get('to_address', 'Desconhecido')}
    Assunto: {email_data.get('subject', 'Sem assunto')}
    
    Corpo do e-mail:
    {email_data.get('body', '')}
    
    Metadados:
    - Recebido em: {email_data.get('received_at', 'Desconhecido')}
    - Thread ID: {email_data.get('thread_id', 'Nova conversa')}
    - Prioridade: {email_data.get('metadata', {}).get('priority', 'normal')}
    - Labels: {', '.join(email_data.get('metadata', {}).get('labels', []))}
    """
    
    try:
        # Configuração de geração
        generation_config = {
            "temperature": settings.GEMINI_TEMPERATURE,
            "top_p": settings.GEMINI_TOP_P,
            "max_output_tokens": settings.GEMINI_MAX_OUTPUT_TOKENS,
            "response_mime_type": "application/json"
        }
        
        # Gera resposta com system instruction e thinking mode
        response = client.models.generate_content(
            model=model or settings.GEMINI_MODEL,
            contents=[
                {"role": "user", "parts": [{"text": user_prompt}]}
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,  # System instruction correta
                thinking_config=types.ThinkingConfig(
                    thinking_budget=-1  # Dynamic thinking mode
                ),
                **generation_config,
                safety_settings=[
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_NONE"
                    }
                ]
            )
        )
        
        # Captura os metadados de uso (tokens)
        usage_metadata = {
            "prompt_tokens": 0,
            "output_tokens": 0,
            "thought_tokens": 0,
            "total_tokens": 0
        }
        
        # Verifica se response tem usage_metadata
        if hasattr(response, 'usage_metadata'):
            metadata = response.usage_metadata
            
            # Captura tokens de prompt/input
            if hasattr(metadata, 'prompt_token_count'):
                usage_metadata["prompt_tokens"] = metadata.prompt_token_count
                
            # Captura tokens de output/candidates
            if hasattr(metadata, 'candidates_token_count'):
                value = metadata.candidates_token_count
                usage_metadata["output_tokens"] = value if value is not None else 0
                
            # Captura tokens de pensamento (para modelos 2.5)
            if hasattr(metadata, 'thoughts_token_count'):
                value = metadata.thoughts_token_count
                usage_metadata["thought_tokens"] = value if value is not None else 0
                
            # Captura total de tokens
            if hasattr(metadata, 'total_token_count'):
                usage_metadata["total_tokens"] = metadata.total_token_count
            else:
                # Calcula total se não fornecido (garantindo valores numéricos)
                usage_metadata["total_tokens"] = (
                    (usage_metadata["prompt_tokens"] or 0) + 
                    (usage_metadata["output_tokens"] or 0) + 
                    (usage_metadata["thought_tokens"] or 0)
                )
        
        logger.info(
            f"Token usage - Prompt: {usage_metadata['prompt_tokens']}, "
            f"Output: {usage_metadata['output_tokens']}, "
            f"Thought: {usage_metadata['thought_tokens']}, "
            f"Total: {usage_metadata['total_tokens']}"
        )
        
        # Extrai e valida JSON da resposta com tratamento seguro
        result_text = None
        
        # Primeiro tenta response.text
        if hasattr(response, 'text') and response.text:
            result_text = response.text
        # Depois tenta via candidates
        elif hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                result_text = part.text
                                break
                    elif hasattr(candidate.content, 'text') and candidate.content.text:
                        result_text = candidate.content.text
                if result_text:
                    break
        
        if not result_text:
            # Verifica se foi truncado por MAX_TOKENS
            if response.candidates and response.candidates[0].finish_reason:
                finish_reason = str(response.candidates[0].finish_reason)
                if 'MAX_TOKENS' in finish_reason:
                    logger.error(f"Response truncated due to MAX_TOKENS limit. Consider increasing max_output_tokens.")
                    raise ValueError("Response truncated - increase max_output_tokens in config")
            logger.error("No text found in response")
            raise ValueError("No text content in Gemini response")
        
        # Tenta fazer parse do JSON
        try:
            result = json.loads(result_text)
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao fazer parse do JSON do Gemini: {e}")
            logger.error(f"Resposta raw: {result_text}")
            
            # Tenta extrair JSON de dentro do texto se houver
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                except:
                    raise ValueError("Resposta do Gemini não está em formato JSON válido")
            else:
                raise ValueError("Resposta do Gemini não contém JSON")
        
        # Log do resultado parseado (genérico, sem validação específica)
        logger.info(f"JSON parseado com sucesso do Gemini")
        
        # Adiciona os metadados de uso ao resultado
        result["usage_metadata"] = usage_metadata
        
        return result
        
    except Exception as e:
        logger.error(f"Erro ao analisar e-mail com Gemini: {e}")
        raise


def test_gemini_connection() -> bool:
    """
    Testa a conexão com o Gemini API
    """
    try:
        client = get_gemini_client()
        
        # Teste simples
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents="Responda apenas com 'OK' se você está funcionando.",
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=10
            )
        )
        
        return "OK" in response.text.upper()
        
    except Exception as e:
        logger.error(f"Erro ao testar conexão com Gemini: {e}")
        return False


def get_model_info(model_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Obtém informações sobre o modelo Gemini
    """
    try:
        client = get_gemini_client()
        model = model_name or settings.GEMINI_MODEL
        
        # Por enquanto, retorna informações básicas
        # A API pode ter métodos específicos para isso no futuro
        return {
            "model": model,
            "available": True,
            "features": {
                "json_mode": True,
                "system_prompts": True,
                "streaming": True,
                "max_tokens": 8192
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter informações do modelo: {e}")
        return {
            "model": model_name or settings.GEMINI_MODEL,
            "available": False,
            "error": str(e)
        }