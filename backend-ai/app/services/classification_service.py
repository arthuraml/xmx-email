"""
Serviço de classificação de e-mails usando Google Gemini
"""

import time
import os
from typing import Dict, Any, Optional, List
from loguru import logger

from ..core.gemini import get_gemini_client
from ..core.config import settings
from ..models.classification import (
    EmailClassificationInput,
    EmailClassificationResult,
    ClassificationType,
    BatchClassificationResult
)
from ..db.supabase import get_supabase
from google import genai
import json


class ClassificationService:
    """
    Serviço para classificar e-mails usando Gemini AI
    """
    
    def __init__(self):
        self.classification_prompt: Optional[str] = None
    
    def _load_classification_prompt(self) -> str:
        """
        Carrega o prompt de classificação do arquivo
        """
        if self.classification_prompt:
            return self.classification_prompt
        
        try:
            prompt_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'prompts',
                'classification_prompt.txt'
            )
            
            with open(prompt_path, 'r', encoding='utf-8') as f:
                self.classification_prompt = f.read().strip()
            
            logger.info("Classification prompt loaded successfully")
            return self.classification_prompt
            
        except Exception as e:
            logger.error(f"Failed to load classification prompt: {e}")
            raise
    
    async def classify_email(
        self,
        email: EmailClassificationInput,
        save_to_db: bool = True
    ) -> EmailClassificationResult:
        """
        Classifica um e-mail usando Gemini AI
        
        Args:
            email: Dados do e-mail para classificar
            save_to_db: Se deve salvar no banco
            
        Returns:
            Resultado da classificação
        """
        start_time = time.time()
        
        try:
            # Prepara prompt
            system_prompt = self._load_classification_prompt()
            
            user_prompt = f"""
            Analise o seguinte e-mail:
            
            De: {email.from_address}
            Para: {email.to_address}
            Assunto: {email.subject}
            
            Corpo do e-mail:
            {email.body}
            
            Data de recebimento: {email.received_at.isoformat()}
            Thread ID: {email.thread_id or 'Nova conversa'}
            """
            
            # Chama Gemini
            client = get_gemini_client()
            
            generation_config = {
                "temperature": 0.2,  # Baixa para classificação consistente
                "top_p": 0.9,
                "max_output_tokens": 500,
                "response_mime_type": "application/json"
            }
            
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
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
            
            # Parse resposta
            result_text = response.text
            classification_data = json.loads(result_text)
            
            # Calcula tempo de processamento
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Captura metadados de tokens
            token_metadata = self._extract_token_metadata(response)
            
            # Determina tipo de classificação
            classification_type = ClassificationType.NONE
            if classification_data['is_support'] and classification_data['is_tracking']:
                classification_type = ClassificationType.BOTH
            elif classification_data['is_support']:
                classification_type = ClassificationType.SUPPORT
            elif classification_data['is_tracking']:
                classification_type = ClassificationType.TRACKING
            
            # Cria resultado
            result = EmailClassificationResult(
                email_id=email.email_id,
                is_support=classification_data['is_support'],
                is_tracking=classification_data['is_tracking'],
                classification_type=classification_type,
                sender_email=classification_data['sender_email'],
                email_type=classification_data['email_type'],
                urgency=classification_data['urgency'],
                confidence=float(classification_data['confidence']),
                reason=classification_data['reason'],
                key_phrases=classification_data.get('key_phrases', []),
                processing_time_ms=processing_time_ms,
                prompt_tokens=token_metadata.get('prompt_tokens'),
                output_tokens=token_metadata.get('output_tokens'),
                total_tokens=token_metadata.get('total_tokens'),
                saved_to_db=False
            )
            
            # Salva no banco se solicitado
            if save_to_db:
                await self._save_to_database(email, result)
                result.saved_to_db = True
            
            logger.info(
                f"Email {email.email_id} classified - "
                f"Support: {result.is_support}, "
                f"Tracking: {result.is_tracking}, "
                f"Confidence: {result.confidence:.2f}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error classifying email {email.email_id}: {e}")
            
            # Retorna resultado de erro
            return EmailClassificationResult(
                email_id=email.email_id,
                is_support=False,
                is_tracking=False,
                classification_type=ClassificationType.NONE,
                sender_email=email.from_address,
                email_type="other",
                urgency="low",
                confidence=0.0,
                reason="Erro na classificação",
                processing_time_ms=int((time.time() - start_time) * 1000),
                error=str(e),
                saved_to_db=False
            )
    
    async def classify_batch(
        self,
        emails: List[EmailClassificationInput],
        save_to_db: bool = True
    ) -> BatchClassificationResult:
        """
        Classifica múltiplos e-mails em lote
        
        Args:
            emails: Lista de e-mails para classificar
            save_to_db: Se deve salvar no banco
            
        Returns:
            Resultado da classificação em lote
        """
        import asyncio
        start_time = time.time()
        
        results = []
        successful = 0
        failed = 0
        
        # Processa em paralelo com limite
        MAX_CONCURRENT = 5
        
        for i in range(0, len(emails), MAX_CONCURRENT):
            batch = emails[i:i + MAX_CONCURRENT]
            
            # Processa batch em paralelo
            batch_tasks = [
                self.classify_email(email, save_to_db)
                for email in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    failed += 1
                    logger.error(f"Batch classification error: {result}")
                else:
                    results.append(result)
                    if not result.error:
                        successful += 1
                    else:
                        failed += 1
            
            # Pequeno delay entre batches
            if i + MAX_CONCURRENT < len(emails):
                await asyncio.sleep(0.5)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return BatchClassificationResult(
            total_emails=len(emails),
            successful=successful,
            failed=failed,
            results=results,
            processing_time_ms=processing_time_ms
        )
    
    def _extract_token_metadata(self, response) -> Dict[str, int]:
        """
        Extrai metadados de tokens da resposta do Gemini
        """
        metadata = {
            "prompt_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0
        }
        
        if hasattr(response, 'usage_metadata'):
            usage = response.usage_metadata
            
            if hasattr(usage, 'prompt_token_count'):
                metadata["prompt_tokens"] = usage.prompt_token_count
            
            if hasattr(usage, 'candidates_token_count'):
                metadata["output_tokens"] = usage.candidates_token_count
            
            if hasattr(usage, 'total_token_count'):
                metadata["total_tokens"] = usage.total_token_count
            else:
                metadata["total_tokens"] = metadata["prompt_tokens"] + metadata["output_tokens"]
        
        return metadata
    
    async def _save_to_database(
        self,
        email: EmailClassificationInput,
        result: EmailClassificationResult
    ):
        """
        Salva resultado da classificação no Supabase
        """
        try:
            supabase = get_supabase()
            
            # Prepara dados para inserção
            data = {
                "email_id": email.email_id,
                "from_address": email.from_address,
                "to_address": email.to_address,
                "subject": email.subject,
                "body": email.body,
                "thread_id": email.thread_id,
                "received_at": email.received_at.isoformat(),
                "is_support": result.is_support,
                "is_tracking": result.is_tracking,
                "classification_confidence": result.confidence,
                "email_type": result.email_type,
                "urgency": result.urgency,
                "processing_time_ms": result.processing_time_ms,
                "prompt_tokens": result.prompt_tokens,
                "output_tokens": result.output_tokens,
                "total_tokens": result.total_tokens,
                "status": "classified"
            }
            
            # Insere ou atualiza
            response = supabase.table("processed_emails").upsert(
                data,
                on_conflict="email_id"
            ).execute()
            
            logger.info(f"Classification saved to database for email {email.email_id}")
            
        except Exception as e:
            logger.error(f"Failed to save classification to database: {e}")
            raise


# Instância singleton do serviço
classification_service = ClassificationService()