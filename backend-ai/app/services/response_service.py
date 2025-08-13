"""
Serviço de geração de respostas usando Google Gemini
"""

import time
import os
import json
from typing import Dict, Any, Optional, List
from loguru import logger

from ..core.gemini import get_gemini_client
from ..core.config import settings
from ..models.response_generation import (
    ResponseGenerationInput,
    GeneratedResponse,
    ResponseTone,
    BatchResponseGenerationResult
)
from ..models.classification import ClassificationType
from ..models.processing import TokenUsage
from ..db.supabase import get_supabase
from .cost_service import cost_service
from google import genai
from google.genai import types


class ResponseService:
    """
    Serviço para gerar respostas de e-mail usando Gemini AI
    """
    
    def __init__(self):
        self.support_prompt: Optional[str] = None
        self.combined_prompt: Optional[str] = None
    
    def _load_prompt(self, prompt_type: str) -> str:
        """
        Carrega o prompt apropriado do arquivo
        
        Args:
            prompt_type: 'support' ou 'combined'
        """
        try:
            if prompt_type == 'support' and self.support_prompt:
                return self.support_prompt
            elif prompt_type == 'combined' and self.combined_prompt:
                return self.combined_prompt
            
            filename = f"{prompt_type}_response_prompt.txt"
            prompt_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'prompts',
                filename
            )
            
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # Cache o prompt
            if prompt_type == 'support':
                self.support_prompt = content
            else:
                self.combined_prompt = content
            
            logger.info(f"{prompt_type} prompt loaded successfully")
            return content
            
        except Exception as e:
            logger.error(f"Failed to load {prompt_type} prompt: {e}")
            raise
    
    async def generate_response(
        self,
        request: ResponseGenerationInput,
        save_to_db: bool = True
    ) -> GeneratedResponse:
        """
        Gera resposta para e-mail usando Gemini AI
        
        Args:
            request: Dados para geração da resposta
            save_to_db: Se deve salvar no banco
            
        Returns:
            Resposta gerada
        """
        start_time = time.time()
        
        try:
            # Determina tipo de resposta
            is_support = request.classification.get('is_support', False)
            is_tracking = request.classification.get('is_tracking', False)
            has_tracking_data = request.tracking_data and request.tracking_data.get('found', False)
            
            if is_support and is_tracking and has_tracking_data:
                response_type = 'combined'
                system_prompt = self._load_prompt('combined')
            else:
                response_type = 'support'
                system_prompt = self._load_prompt('support')
            
            # Prepara contexto para LLM
            user_prompt = self._build_user_prompt(request, response_type)
            
            # Chama Gemini
            client = get_gemini_client()
            
            generation_config = {
                "temperature": 0.3,  # Balanceado para respostas (um pouco de criatividade)
                "top_p": 0.95,
                "max_output_tokens": 65000,  # Máximo para respostas completas
                "response_mime_type": "application/json"
            }
            
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
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
            
            # Parse resposta com tratamento seguro
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
                        logger.error(f"Response generation truncated due to MAX_TOKENS limit")
                        raise ValueError("Response truncated - increase max_output_tokens")
                logger.error("No text found in response generation")
                raise ValueError("No text content in Gemini response")
            response_data = json.loads(result_text)
            
            # Calcula tempo de processamento
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Captura metadados de tokens
            token_metadata = self._extract_token_metadata(response)
            
            # Calcula custos se temos dados de tokens
            costs = None
            if token_metadata.get('total_tokens', 0) > 0:
                token_usage = TokenUsage(
                    input_tokens=token_metadata.get('prompt_tokens', 0),
                    output_tokens=token_metadata.get('output_tokens', 0),
                    thought_tokens=token_metadata.get('thought_tokens', 0),
                    total_tokens=token_metadata.get('total_tokens', 0)
                )
                costs = await cost_service.calculate_costs(
                    token_usage=token_usage,
                    model_name="gemini-2.5-flash"
                )
            
            # Cria resposta
            generated = GeneratedResponse(
                email_id=request.email_id,
                suggested_subject=response_data['subject'],
                suggested_body=response_data['body'],
                tone=ResponseTone(response_data.get('tone', 'professional')),
                addresses_support=response_data.get('addresses_support', is_support),
                addresses_tracking=response_data.get('addresses_tracking', is_tracking),
                tracking_included=response_data.get('tracking_included'),
                priority_actions=response_data.get('priority_actions', []),
                requires_followup=response_data.get('requires_followup', False),
                internal_notes=response_data.get('internal_notes'),
                response_type=response_type,
                confidence=0.95,  # Alta confiança para respostas geradas
                processing_time_ms=processing_time_ms,
                prompt_tokens=token_metadata.get('prompt_tokens'),
                output_tokens=token_metadata.get('output_tokens'),
                total_tokens=token_metadata.get('total_tokens'),
                saved_to_db=False
            )
            
            # Salva no banco se solicitado
            if save_to_db:
                await self._save_to_database(generated, request, costs)
                generated.saved_to_db = True
            
            logger.info(
                f"Response generated for email {request.email_id} - "
                f"Type: {response_type}, "
                f"Time: {processing_time_ms}ms"
            )
            
            return generated
            
        except Exception as e:
            logger.error(f"Error generating response for email {request.email_id}: {e}")
            # Re-raise the exception to let the API endpoint handle it with proper HTTP status
            raise
    
    def _build_user_prompt(
        self,
        request: ResponseGenerationInput,
        response_type: str
    ) -> str:
        """
        Constrói prompt do usuário com contexto completo
        """
        email = request.email_content
        classification = request.classification
        
        prompt = f"""
        CONTEXTO DO E-MAIL:
        De: {email.get('from', 'Desconhecido')}
        Para: {email.get('to', 'Desconhecido')}
        Assunto: {email.get('subject', 'Sem assunto')}
        
        Corpo do e-mail:
        {email.get('body', '')}
        
        CLASSIFICAÇÃO:
        - É suporte: {classification.get('is_support', False)}
        - É rastreamento: {classification.get('is_tracking', False)}
        - Urgência: {classification.get('urgency', 'normal')}
        - Tipo: {classification.get('email_type', 'other')}
        """
        
        # Adiciona dados de rastreamento se disponível
        if request.tracking_data and response_type == 'combined':
            tracking_data = request.tracking_data
            
            # Verifica se tem dados de rastreamento
            if tracking_data.get('found') and tracking_data.get('orders'):
                prompt += "\n\n        DADOS DE RASTREAMENTO DISPONÍVEIS:"
                
                # Processa cada pedido encontrado
                for order in tracking_data['orders'][:3]:  # Limita a 3 pedidos
                    prompt += f"""
        
        PEDIDO {order.get('order_id', 'N/A')}:
        - Código de rastreamento: {order.get('tracking_code', 'Não disponível')}
        - Data da compra: {order.get('purchase_date', 'Não disponível')}
        - Status: {order.get('status', 'Em processamento')}
        """
            else:
                prompt += """
        
        RASTREAMENTO:
        Não foram encontrados pedidos com rastreamento para este e-mail.
        Orientação: Solicitar ao cliente o número do pedido ou verificar o e-mail de cadastro.
        """
        
        elif response_type == 'combined' and not request.tracking_data:
            prompt += """
        
        OBSERVAÇÃO: Cliente solicitou rastreamento mas não foram encontrados dados no sistema.
        Informe que estamos verificando e solicite informações adicionais (número do pedido, nota fiscal, etc).
        """
        
        # Adiciona instruções especiais se houver
        if request.priority_message:
            prompt += f"\n\nMENSAGEM PRIORITÁRIA PARA INCLUIR: {request.priority_message}"
        
        if request.custom_tone:
            prompt += f"\n\nTOM SOLICITADO: {request.custom_tone.value}"
        
        prompt += "\n\nGere uma resposta apropriada seguindo as diretrizes do prompt."
        
        return prompt
    
    def _extract_token_metadata(self, response) -> Dict[str, int]:
        """
        Extrai metadados de tokens da resposta do Gemini
        """
        metadata = {
            "prompt_tokens": 0,
            "output_tokens": 0,
            "thought_tokens": 0,
            "total_tokens": 0
        }
        
        if hasattr(response, 'usage_metadata'):
            usage = response.usage_metadata
            
            if hasattr(usage, 'prompt_token_count'):
                metadata["prompt_tokens"] = usage.prompt_token_count
            
            if hasattr(usage, 'candidates_token_count'):
                metadata["output_tokens"] = usage.candidates_token_count
            
            # Captura thinking tokens se disponível
            if hasattr(usage, 'thought_token_count'):
                metadata["thought_tokens"] = usage.thought_token_count
            
            if hasattr(usage, 'total_token_count'):
                metadata["total_tokens"] = usage.total_token_count
            else:
                metadata["total_tokens"] = (
                    metadata["prompt_tokens"] + 
                    metadata["output_tokens"] + 
                    metadata["thought_tokens"]
                )
        
        return metadata
    
    async def _save_to_database(
        self,
        response: GeneratedResponse,
        request: ResponseGenerationInput,
        costs: Optional[Dict[str, Any]] = None
    ):
        """
        Salva resposta gerada no Supabase
        """
        try:
            supabase = get_supabase()
            
            # Prepara dados para inserção
            data = {
                "email_id": response.email_id,
                "response_type": response.response_type,
                "suggested_subject": response.suggested_subject,
                "suggested_body": response.suggested_body,
                "tone": response.tone.value,
                "tracking_data": response.tracking_included,
                "approved": False,
                "sent": False,
                "confidence": response.confidence,
                "reason": response.internal_notes
            }
            
            # Adiciona custos se disponíveis
            if costs:
                data.update({
                    "cost_input_usd": costs["cost_input_usd"],
                    "cost_output_usd": costs["cost_output_usd"],
                    "cost_thinking_usd": costs["cost_thinking_usd"],
                    "cost_total_usd": costs["cost_total_usd"],
                    "cost_input_brl": costs["cost_input_brl"],
                    "cost_output_brl": costs["cost_output_brl"],
                    "cost_thinking_brl": costs["cost_thinking_brl"],
                    "cost_total_brl": costs["cost_total_brl"],
                    "exchange_rate": costs["exchange_rate"]
                })
            
            # Insere nova resposta (permite múltiplas respostas por email para auditoria)
            result = supabase.table("llm_responses").insert(data).execute()
            
            logger.info(f"Response saved to database for email {response.email_id}")
            
        except Exception as e:
            logger.error(f"Failed to save response to database: {e}")
            raise
    
    async def generate_batch(
        self,
        requests: List[ResponseGenerationInput],
        save_to_db: bool = True
    ) -> BatchResponseGenerationResult:
        """
        Gera respostas para múltiplos e-mails em lote
        """
        import asyncio
        start_time = time.time()
        
        responses = []
        successful = 0
        failed = 0
        
        # Processa em paralelo com limite
        MAX_CONCURRENT = 3  # Menos paralelo para geração de resposta
        
        for i in range(0, len(requests), MAX_CONCURRENT):
            batch = requests[i:i + MAX_CONCURRENT]
            
            # Processa batch em paralelo
            batch_tasks = [
                self.generate_response(req, save_to_db)
                for req in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    failed += 1
                    logger.error(f"Batch generation error: {result}")
                else:
                    responses.append(result)
                    if not result.error:
                        successful += 1
                    else:
                        failed += 1
            
            # Delay entre batches
            if i + MAX_CONCURRENT < len(requests):
                await asyncio.sleep(1.0)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return BatchResponseGenerationResult(
            total_requests=len(requests),
            successful=successful,
            failed=failed,
            responses=responses,
            processing_time_ms=processing_time_ms
        )


# Instância singleton do serviço
response_service = ResponseService()