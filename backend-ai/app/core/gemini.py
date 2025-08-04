"""
Configuração e cliente do Google Gemini
"""

from google import genai
from typing import Optional, Dict, Any
import json
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
        
        # Gera resposta
        response = client.models.generate_content(
            model=model or settings.GEMINI_MODEL,
            contents=[
                {"role": "system", "parts": [{"text": system_prompt}]},
                {"role": "user", "parts": [{"text": user_prompt}]}
            ],
            config=genai.types.GenerateContentConfig(
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
        
        # Extrai e valida JSON da resposta
        result_text = response.text
        
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
        
        # Valida campos obrigatórios
        required_fields = ["decision", "confidence", "email_type", "urgency", "reason"]
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Campo obrigatório '{field}' não encontrado na resposta")
        
        # Valida decision
        if result["decision"] not in ["respond", "ignore"]:
            raise ValueError(f"Decisão inválida: {result['decision']}")
        
        # Valida confidence
        if not isinstance(result["confidence"], (int, float)) or not 0 <= result["confidence"] <= 1:
            raise ValueError(f"Confidence inválido: {result['confidence']}")
        
        # Se decision=respond, valida suggested_response
        if result["decision"] == "respond":
            if "suggested_response" not in result:
                raise ValueError("suggested_response é obrigatório quando decision=respond")
            
            sr = result["suggested_response"]
            if not isinstance(sr, dict) or "subject" not in sr or "body" not in sr:
                raise ValueError("suggested_response deve conter 'subject' e 'body'")
        
        logger.info(
            f"E-mail analisado com sucesso - "
            f"Decisão: {result['decision']}, "
            f"Confiança: {result['confidence']:.2f}"
        )
        
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
            config=genai.types.GenerateContentConfig(
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