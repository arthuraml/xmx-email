"""
Serviço de integração com Google Gemini
"""

import time
from typing import Dict, Any, Optional, List
from loguru import logger

from ..core.gemini import analyze_email_with_gemini, test_gemini_connection
from ..core.config import settings
from ..models.email import EmailInput
from ..models.response import (
    GeminiDecision,
    EmailProcessingResult,
    ProcessingStatus,
    DecisionType,
    EmailType,
    ResponseTone,
    SuggestedResponse
)


class GeminiService:
    """
    Serviço para processar e-mails com Google Gemini
    """
    
    def __init__(self):
        self.default_prompt = None  # Carregado sob demanda
    
    async def process_email(
        self,
        email: EmailInput,
        system_prompt: Optional[str] = None,
        custom_model: Optional[str] = None
    ) -> EmailProcessingResult:
        """
        Processa um e-mail usando o Gemini AI
        
        Args:
            email: E-mail para processar
            system_prompt: Prompt customizado (opcional)
            custom_model: Modelo específico (opcional)
        
        Returns:
            Resultado do processamento
        """
        start_time = time.time()
        
        try:
            # Prepara dados do e-mail
            email_data = {
                "from_address": email.from_address,
                "to_address": email.to_address,
                "subject": email.subject,
                "body": email.body,
                "thread_id": email.thread_id,
                "received_at": email.received_at.isoformat(),
                "metadata": email.metadata.model_dump() if email.metadata else {}
            }
            
            # Usa prompt padrão se não fornecido
            if system_prompt:
                prompt = system_prompt
            else:
                # Usa um prompt padrão básico se não fornecido
                if self.default_prompt is None:
                    self.default_prompt = """
                    Você é um assistente de análise de e-mails.
                    Analise o e-mail e determine se deve ser respondido ou ignorado.
                    Retorne sua análise em formato JSON.
                    """
                prompt = self.default_prompt
            
            # Analisa com Gemini
            gemini_result = await analyze_email_with_gemini(
                email_data=email_data,
                system_prompt=prompt,
                model=custom_model
            )
            
            # Converte resultado para modelos Pydantic
            decision = self._parse_gemini_response(gemini_result)
            
            # Extrai metadados de uso (tokens)
            usage_metadata = gemini_result.get("usage_metadata", {})
            
            # Calcula tempo de processamento
            processing_time = time.time() - start_time
            
            # Cria resultado
            return EmailProcessingResult(
                status=ProcessingStatus.COMPLETED,
                email_id=email.email_id,
                decision=decision.decision,
                confidence=decision.confidence,
                reason=decision.reason,
                suggested_response=decision.suggested_response,
                processing_time=processing_time,
                prompt_tokens=usage_metadata.get("prompt_tokens"),
                output_tokens=usage_metadata.get("output_tokens"),
                thought_tokens=usage_metadata.get("thought_tokens"),
                total_tokens=usage_metadata.get("total_tokens")
            )
            
        except Exception as e:
            logger.error(f"Erro ao processar e-mail {email.email_id}: {e}")
            
            # Retorna resultado de erro
            return EmailProcessingResult(
                status=ProcessingStatus.FAILED,
                email_id=email.email_id,
                processing_time=time.time() - start_time,
                error=str(e)
            )
    
    def _parse_gemini_response(self, response: Dict[str, Any]) -> GeminiDecision:
        """
        Converte resposta do Gemini para modelo Pydantic
        """
        try:
            # Parse da resposta sugerida se existir
            suggested_response = None
            if response.get("decision") == "respond" and "suggested_response" in response:
                sr_data = response["suggested_response"]
                suggested_response = SuggestedResponse(
                    subject=sr_data.get("subject", ""),
                    body=sr_data.get("body", ""),
                    tone=ResponseTone(sr_data.get("tone", "professional"))
                )
            
            # Cria decisão
            return GeminiDecision(
                decision=DecisionType(response["decision"]),
                confidence=float(response["confidence"]),
                email_type=EmailType(response.get("email_type", "other")),
                urgency=response.get("urgency", "normal"),
                reason=response["reason"],
                suggested_response=suggested_response
            )
            
        except Exception as e:
            logger.error(f"Erro ao fazer parse da resposta do Gemini: {e}")
            logger.error(f"Resposta raw: {response}")
            raise ValueError(f"Resposta inválida do Gemini: {e}")
    
    async def test_connection(self) -> bool:
        """
        Testa conexão com Gemini API
        """
        return test_gemini_connection()
    
    async def process_batch(
        self,
        emails: List[EmailInput],
        system_prompt: Optional[str] = None,
        max_concurrent: int = 5
    ) -> List[EmailProcessingResult]:
        """
        Processa múltiplos e-mails em lote
        
        Args:
            emails: Lista de e-mails para processar
            system_prompt: Prompt customizado
            max_concurrent: Máximo de processamentos simultâneos
        
        Returns:
            Lista de resultados
        """
        import asyncio
        
        results = []
        
        # Processa em lotes para evitar rate limit
        for i in range(0, len(emails), max_concurrent):
            batch = emails[i:i + max_concurrent]
            
            # Processa batch em paralelo
            batch_tasks = [
                self.process_email(email, system_prompt)
                for email in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Converte exceções em resultados de erro
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    results.append(
                        EmailProcessingResult(
                            status=ProcessingStatus.FAILED,
                            email_id=batch[j].email_id,
                            processing_time=0.0,
                            error=str(result)
                        )
                    )
                else:
                    results.append(result)
            
            # Pequeno delay entre batches para evitar rate limit
            if i + max_concurrent < len(emails):
                await asyncio.sleep(0.5)
        
        return results
    
    def validate_prompt(self, prompt: str) -> bool:
        """
        Valida se um prompt tem os elementos necessários
        """
        required_elements = [
            "decision",
            "confidence",
            "email_type",
            "urgency",
            "reason",
            "respond",
            "ignore"
        ]
        
        prompt_lower = prompt.lower()
        
        # Verifica se elementos necessários estão presentes
        missing = [elem for elem in required_elements if elem not in prompt_lower]
        
        if missing:
            logger.warning(f"Prompt pode estar incompleto. Elementos faltando: {missing}")
            return False
        
        return True


# Instância singleton do serviço
gemini_service = GeminiService()