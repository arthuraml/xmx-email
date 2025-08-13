"""
Serviço unificado de processamento de e-mails
Integra classificação e busca de rastreamento
"""

import time
import re
from typing import Optional, Dict, Any, List
from loguru import logger

from ..core.gemini import analyze_email_with_gemini
from ..db.supabase import save_processed_email
from ..models.email import EmailInput
from ..models.processing import (
    EmailClassification,
    TrackingInfo,
    TrackingResult,
    TokenUsage,
    EmailProcessingResponse
)
from .mysql_service import mysql_service
from .cost_service import cost_service


class ProcessingService:
    """
    Serviço unificado para processar e-mails
    """
    
    def __init__(self):
        self.classification_prompt = None
    
    def _get_classification_prompt(self) -> str:
        """
        Retorna o prompt para classificação de e-mails
        """
        if self.classification_prompt is None:
            self.classification_prompt = """
Você é um assistente de classificação de e-mails para suporte ao cliente.

Analise o e-mail fornecido e determine:

1. **is_support**: Se é uma solicitação de suporte ao cliente (true/false)
2. **is_tracking**: Se o cliente está perguntando sobre rastreamento/status de pedido (true/false)
3. **urgency**: Nível de urgência (low, medium, high)
4. **email_type**: Tipo do e-mail (question, complaint, request, spam, newsletter, auto_reply, other)
5. **confidence**: Sua confiança na classificação (0.0 a 1.0)
6. **extracted_order_id**: Se houver menção a número de pedido, extraia-o

IMPORTANTE:
- E-mails sobre "onde está meu pedido", "status da entrega", "rastreamento", "tracking" devem ter is_tracking=true
- E-mails com perguntas sobre produtos, problemas, reclamações devem ter is_support=true
- Um e-mail pode ser AMBOS support E tracking
- Procure por números de pedido no formato: números longos, códigos alfanuméricos, menções a "pedido #X"

Responda APENAS em formato JSON válido:
{
    "is_support": boolean,
    "is_tracking": boolean,
    "urgency": "low|medium|high",
    "email_type": "question|complaint|request|spam|newsletter|auto_reply|other",
    "confidence": 0.0-1.0,
    "extracted_order_id": "string ou null"
}
"""
        return self.classification_prompt
    
    def _extract_order_id_from_text(self, text: str) -> Optional[str]:
        """
        Tenta extrair ID de pedido do texto do e-mail
        """
        # Padrões comuns de ID de pedido
        patterns = [
            r'pedido\s*#?\s*(\d{5,})',  # Pedido #12345
            r'order\s*#?\s*(\d{5,})',    # Order #12345
            r'código\s*:\s*(\w{8,})',    # Código: ABC12345
            r'rastreamento\s*:\s*(\w{8,})',  # Rastreamento: XYZ789
            r'\b(\d{8,12})\b',           # Números longos isolados
            r'\b([A-Z0-9]{8,15})\b'      # Códigos alfanuméricos
        ]
        
        text_lower = text.lower()
        for pattern in patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        return None
    
    async def process_email(
        self,
        email: EmailInput,
        custom_prompt: Optional[str] = None
    ) -> EmailProcessingResponse:
        """
        Processa um e-mail: classifica e busca rastreamento se necessário
        
        Args:
            email: E-mail para processar
            custom_prompt: Prompt customizado (opcional)
        
        Returns:
            Resposta unificada do processamento
        """
        start_time = time.time()
        
        try:
            # Fase 1: Classificação via Gemini
            logger.info(f"Processing email {email.email_id} from {email.from_address}")
            
            # Prepara dados do e-mail
            email_data = {
                "from_address": email.from_address,
                "to_address": email.to_address,
                "subject": email.subject,
                "body": email.body,
                "received_at": email.received_at.isoformat() if email.received_at else None
            }
            
            # Usa prompt de classificação
            prompt = custom_prompt or self._get_classification_prompt()
            
            # Classifica com Gemini
            gemini_result = await analyze_email_with_gemini(
                email_data=email_data,
                system_prompt=prompt,
                model=None
            )
            
            # Parse da classificação
            classification = self._parse_classification(gemini_result)
            
            # Se não encontrou order_id na classificação, tenta extrair do texto
            if not classification.extracted_order_id:
                full_text = f"{email.subject} {email.body}"
                classification.extracted_order_id = self._extract_order_id_from_text(full_text)
            
            # Extrai tokens usados
            usage_metadata = gemini_result.get("usage_metadata", {})
            tokens = TokenUsage(
                input_tokens=usage_metadata.get("prompt_tokens", 0),
                output_tokens=usage_metadata.get("output_tokens", 0),
                thought_tokens=usage_metadata.get("thought_tokens", 0),
                total_tokens=usage_metadata.get("total_tokens", 0)
            )
            
            # Fase 2: Busca de rastreamento se necessário
            tracking_result = None
            if classification.is_tracking:
                logger.info(f"Email classified as tracking request, searching database...")
                tracking_result = await self._search_tracking(
                    sender_email=email.from_address,
                    order_id=classification.extracted_order_id
                )
            
            # Calcula tempo total
            processing_time = time.time() - start_time
            
            # Calcula custos do processamento
            costs = await cost_service.calculate_costs(
                token_usage=tokens,
                model_name="gemini-2.5-flash"
            )
            
            # Salva email processado no banco de dados
            email_record = {
                "email_id": email.email_id,
                "from_address": email.from_address,
                "to_address": email.to_address,
                "subject": email.subject,
                "body": email.body,
                "thread_id": email.thread_id,
                "received_at": email.received_at.isoformat() if email.received_at else None,
                "is_support": classification.is_support,
                "is_tracking": classification.is_tracking,
                "classification_confidence": float(classification.confidence),
                "email_type": classification.email_type,
                "urgency": classification.urgency,
                "processing_time_ms": int(processing_time * 1000),
                "prompt_tokens": tokens.input_tokens,
                "output_tokens": tokens.output_tokens,
                "thought_tokens": tokens.thought_tokens,
                "total_tokens": tokens.total_tokens,
                # Adiciona campos de custo
                "cost_input_usd": costs["cost_input_usd"],
                "cost_output_usd": costs["cost_output_usd"],
                "cost_thinking_usd": costs["cost_thinking_usd"],
                "cost_total_usd": costs["cost_total_usd"],
                "cost_input_brl": costs["cost_input_brl"],
                "cost_output_brl": costs["cost_output_brl"],
                "cost_thinking_brl": costs["cost_thinking_brl"],
                "cost_total_brl": costs["cost_total_brl"],
                "exchange_rate": costs["exchange_rate"],
                "status": "processed"
            }
            
            try:
                save_processed_email(email_record)
                logger.info(f"Email {email.email_id} saved to processed_emails table")
                
                # Se foi rastreamento, salva também na tabela tracking_requests
                if classification.is_tracking and tracking_result:
                    from ..db.supabase import get_supabase
                    supabase = get_supabase()
                    
                    tracking_record = {
                        "email_id": email.email_id,
                        "sender_email": email.from_address,
                        "order_id": classification.extracted_order_id,
                        "mysql_queried": tracking_result.found,
                        "query_success": tracking_result.found,
                        "tracking_details": {
                            "found": tracking_result.found,
                            "orders": [
                                {
                                    "order_id": order.order_id,
                                    "tracking_code": order.tracking_code,
                                    "status": order.status,
                                    "purchase_date": order.purchase_date.isoformat() if order.purchase_date else None,
                                    "customer_email": order.customer_email
                                } for order in tracking_result.orders
                            ] if tracking_result.orders else []
                        }
                    }
                    
                    try:
                        supabase.table("tracking_requests").insert(tracking_record).execute()
                        logger.info(f"Tracking request saved for email {email.email_id}")
                    except Exception as tracking_error:
                        logger.error(f"Failed to save tracking request: {tracking_error}")
                        
            except Exception as db_error:
                logger.error(f"Failed to save email {email.email_id} to database: {db_error}")
                # Continue processing even if save fails (non-critical)
            
            # Retorna resposta unificada
            return EmailProcessingResponse(
                email_id=email.email_id,
                classification=classification,
                tracking_data=tracking_result,
                tokens=tokens,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error processing email {email.email_id}: {e}")
            # Re-raise the exception to let the API handle it properly
            raise
    
    def _parse_classification(self, gemini_response: Dict[str, Any]) -> EmailClassification:
        """
        Parse da resposta do Gemini para classificação
        """
        try:
            # Se a resposta já tem os campos corretos
            if "is_support" in gemini_response:
                return EmailClassification(
                    is_support=bool(gemini_response.get("is_support", False)),
                    is_tracking=bool(gemini_response.get("is_tracking", False)),
                    urgency=gemini_response.get("urgency", "medium"),
                    confidence=float(gemini_response.get("confidence", 0.5)),
                    email_type=gemini_response.get("email_type", "other"),
                    extracted_order_id=gemini_response.get("extracted_order_id")
                )
            
            # Compatibilidade com formato antigo
            decision = gemini_response.get("decision", "ignore")
            is_support = decision == "respond"
            
            # Tenta detectar se é tracking pela razão ou tipo
            reason = gemini_response.get("reason", "").lower()
            email_type = gemini_response.get("email_type", "").lower()
            is_tracking = any(word in reason + email_type for word in 
                            ["tracking", "rastreamento", "pedido", "entrega", "order", "status"])
            
            return EmailClassification(
                is_support=is_support,
                is_tracking=is_tracking,
                urgency=gemini_response.get("urgency", "medium"),
                confidence=float(gemini_response.get("confidence", 0.5)),
                email_type=gemini_response.get("email_type", "other"),
                extracted_order_id=None
            )
            
        except Exception as e:
            logger.error(f"Error parsing classification: {e}")
            logger.debug(f"Raw response: {gemini_response}")
            
            # Retorna classificação padrão
            return EmailClassification(
                is_support=True,  # Por segurança, assume que precisa responder
                is_tracking=False,
                urgency="medium",
                confidence=0.3,
                email_type="other"
            )
    
    async def _search_tracking(
        self,
        sender_email: str,
        order_id: Optional[str] = None
    ) -> TrackingResult:
        """
        Busca dados de rastreamento no MySQL
        """
        import time
        start_time = time.time()
        
        try:
            # Busca no MySQL
            if order_id:
                # Busca específica por order_id
                tracking_data = await mysql_service.find_tracking_by_email(
                    email=sender_email,
                    order_id=order_id
                )
                
                if tracking_data:
                    orders = [TrackingInfo(
                        order_id=tracking_data.order_id,
                        tracking_code=tracking_data.tracking_code,
                        purchase_date=tracking_data.last_update,
                        status=tracking_data.status.value if tracking_data.status else None
                    )]
                else:
                    orders = []
            else:
                # Busca todos os pedidos recentes do cliente
                all_trackings = await mysql_service.find_all_trackings_by_email(
                    email=sender_email,
                    limit=5
                )
                
                orders = [
                    TrackingInfo(
                        order_id=t.order_id,
                        tracking_code=t.tracking_code,
                        purchase_date=t.last_update,
                        status=t.status.value if t.status else None
                    )
                    for t in all_trackings
                ]
            
            query_time_ms = int((time.time() - start_time) * 1000)
            
            return TrackingResult(
                found=len(orders) > 0,
                orders=orders,
                query_time_ms=query_time_ms
            )
            
        except Exception as e:
            logger.error(f"Error searching tracking: {e}")
            query_time_ms = int((time.time() - start_time) * 1000)
            
            return TrackingResult(
                found=False,
                orders=[],
                query_time_ms=query_time_ms,
                error=str(e)
            )
    
    async def process_batch(
        self,
        emails: List[EmailInput],
        max_concurrent: int = 5
    ) -> List[EmailProcessingResponse]:
        """
        Processa múltiplos e-mails em lote
        """
        import asyncio
        
        results = []
        
        # Processa em lotes
        for i in range(0, len(emails), max_concurrent):
            batch = emails[i:i + max_concurrent]
            
            # Processa batch em paralelo
            batch_tasks = [
                self.process_email(email)
                for email in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Converte exceções em resultados de erro
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    results.append(
                        EmailProcessingResponse(
                            email_id=batch[j].email_id,
                            classification=EmailClassification(
                                is_support=False,
                                is_tracking=False,
                                urgency="low",
                                confidence=0.0,
                                email_type="other"
                            ),
                            tracking_data=None,
                            tokens=TokenUsage(),
                            processing_time=0.0,
                            error=str(result)
                        )
                    )
                else:
                    results.append(result)
            
            # Delay entre batches
            if i + max_concurrent < len(emails):
                await asyncio.sleep(0.5)
        
        return results


# Instância singleton do serviço
processing_service = ProcessingService()