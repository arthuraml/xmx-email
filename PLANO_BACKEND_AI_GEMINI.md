# Plano de Implementação: Backend FastAPI com Google Gemini

## 📋 Visão Geral do Sistema

O backend AI será responsável por:
1. Receber e-mails do frontend Next.js
2. Processar e-mails usando Google Gemini AI
3. Decidir automaticamente se deve responder ou ignorar
4. Gerar respostas inteligentes quando necessário
5. Armazenar histórico e analytics no Supabase

## 🏗️ Arquitetura Detalhada

### Estrutura de Diretórios
```
xmx-email/
├── backend-ai/                 # Backend Python/FastAPI
│   ├── app/
│   │   ├── __init__.py
│   │   ├── api/               # Endpoints da API
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── emails.py      # Endpoints de processamento
│   │   │       ├── prompts.py     # Gerenciamento de prompts
│   │   │       ├── analytics.py   # Dashboard e estatísticas
│   │   │       └── health.py      # Health check
│   │   ├── core/              # Configurações core
│   │   │   ├── __init__.py
│   │   │   ├── config.py      # Configurações do app
│   │   │   ├── security.py    # Autenticação e segurança
│   │   │   └── gemini.py      # Cliente Gemini configurado
│   │   ├── models/            # Modelos Pydantic
│   │   │   ├── __init__.py
│   │   │   ├── email.py       # Modelos de e-mail
│   │   │   ├── response.py    # Modelos de resposta
│   │   │   └── prompt.py      # Modelos de prompt
│   │   ├── services/          # Lógica de negócios
│   │   │   ├── __init__.py
│   │   │   ├── email_processor.py    # Processamento principal
│   │   │   ├── gemini_service.py     # Integração Gemini
│   │   │   └── response_generator.py # Geração de respostas
│   │   ├── db/                # Database/Supabase
│   │   │   ├── __init__.py
│   │   │   ├── supabase.py    # Cliente Supabase
│   │   │   └── repositories/   # Repositórios de dados
│   │   │       ├── __init__.py
│   │   │       ├── email_repo.py
│   │   │       └── prompt_repo.py
│   │   └── utils/             # Utilitários
│   │       ├── __init__.py
│   │       ├── validators.py
│   │       └── helpers.py
│   ├── tests/                 # Testes unitários
│   │   ├── __init__.py
│   │   ├── test_emails.py
│   │   └── test_gemini.py
│   ├── requirements.txt       # Dependências
│   ├── .env.example          # Exemplo de variáveis
│   ├── Dockerfile            # Para containerização
│   ├── docker-compose.yml    # Orquestração local
│   └── main.py              # Entry point

```

## 🔧 Stack Tecnológica Detalhada

### Core
- **FastAPI**: Framework web assíncrono (latest)
- **Python**: 3.11+ (para melhor performance)
- **Uvicorn**: ASGI server
- **Pydantic V2**: Validação de dados

### AI/LLM
- **google-genai**: SDK oficial do Google Gemini
- **Modelo**: gemini-2.5-flash (rápido e eficiente)

### Database & Cache
- **Supabase**: PostgreSQL para persistência
- **Redis**: Cache e filas (opcional para v2)

### Ferramentas
- **httpx**: Cliente HTTP assíncrono
- **python-dotenv**: Gerenciamento de variáveis
- **loguru**: Logging avançado
- **pytest**: Testes
- **black**: Formatação de código

## 📡 API Endpoints Detalhados

### 1. Processamento de E-mail
```python
POST /api/v1/emails/process
Headers:
  - Authorization: Bearer {API_KEY}
  - Content-Type: application/json

Request Body:
{
  "email_id": "msg_12345",
  "from": "cliente@example.com",
  "to": "support@biofraga.com",
  "subject": "Dúvida sobre produto",
  "body": "Olá, gostaria de saber mais sobre...",
  "thread_id": "thread_123",
  "received_at": "2025-01-15T10:30:00Z",
  "attachments": [],
  "metadata": {
    "priority": "normal",
    "labels": ["INBOX", "UNREAD"]
  }
}

Response (200 OK):
{
  "status": "processed",
  "email_id": "msg_12345",
  "decision": "respond",
  "confidence": 0.92,
  "reason": "Cliente fazendo pergunta direta sobre produto",
  "suggested_response": {
    "subject": "Re: Dúvida sobre produto",
    "body": "Olá! Obrigado por entrar em contato...",
    "draft": true
  },
  "processing_time": 1.234,
  "processed_at": "2025-01-15T10:30:02Z"
}

Response (202 Accepted) - Para processamento assíncrono:
{
  "status": "queued",
  "email_id": "msg_12345",
  "job_id": "job_67890",
  "estimated_time": 5
}
```

### 2. Verificar Status do Processamento
```python
GET /api/v1/emails/{email_id}/status

Response:
{
  "email_id": "msg_12345",
  "status": "completed",
  "decision": "respond",
  "processed_at": "2025-01-15T10:30:02Z",
  "response_sent": false,
  "response_details": {...}
}
```

### 3. Gerenciamento de System Prompts
```python
# Obter prompt atual
GET /api/v1/prompts/current

Response:
{
  "id": "prompt_001",
  "name": "default",
  "system_prompt": "Você é um assistente...",
  "decision_criteria": {
    "respond_to": ["questions", "complaints", "urgent"],
    "ignore": ["spam", "newsletters", "auto-replies"]
  },
  "active": true,
  "created_at": "2025-01-01T00:00:00Z"
}

# Atualizar prompt
PUT /api/v1/prompts/{prompt_id}
{
  "system_prompt": "Novo prompt...",
  "decision_criteria": {...}
}

# Criar novo prompt
POST /api/v1/prompts
{
  "name": "aggressive_responder",
  "system_prompt": "...",
  "decision_criteria": {...}
}
```

### 4. Analytics e Métricas
```python
GET /api/v1/analytics/summary?start_date=2025-01-01&end_date=2025-01-31

Response:
{
  "period": {
    "start": "2025-01-01",
    "end": "2025-01-31"
  },
  "totals": {
    "emails_processed": 1523,
    "emails_responded": 687,
    "emails_ignored": 836,
    "response_rate": 0.451
  },
  "average_metrics": {
    "processing_time_seconds": 1.85,
    "confidence_score": 0.89
  },
  "top_reasons": {
    "respond": [
      {"reason": "direct_question", "count": 234},
      {"reason": "complaint", "count": 156}
    ],
    "ignore": [
      {"reason": "newsletter", "count": 423},
      {"reason": "spam", "count": 201}
    ]
  }
}
```

## 🤖 Integração Google Gemini - Detalhes

### System Prompt Completo
```python
DEFAULT_SYSTEM_PROMPT = """
Você é um assistente inteligente de e-mail para a empresa Biofraga.
Sua função é analisar e-mails recebidos e decidir se devem ser respondidos.

CONTEXTO DA EMPRESA:
- Nome: Biofraga
- Setor: [Definir setor]
- E-mail de suporte: support@biofraga.com

CRITÉRIOS PARA RESPONDER:
1. Perguntas diretas sobre produtos ou serviços
2. Solicitações de suporte ou ajuda
3. Reclamações ou feedbacks negativos
4. E-mails marcados como urgentes ou importantes
5. Solicitações de orçamento ou informações comerciais
6. Confirmações necessárias (agendamentos, pedidos, etc)

CRITÉRIOS PARA IGNORAR:
1. Spam ou e-mails promocionais não solicitados
2. Newsletters e e-mails informativos
3. Respostas automáticas (out of office, etc)
4. E-mails já respondidos na mesma thread
5. Notificações de sistemas
6. E-mails sem conteúdo relevante

ANÁLISE NECESSÁRIA:
1. Identifique o tipo de e-mail
2. Avalie a urgência (alta/média/baixa)
3. Determine se requer resposta
4. Se sim, sugira uma resposta apropriada

FORMATO DE RESPOSTA (JSON):
{
  "decision": "respond" ou "ignore",
  "confidence": 0.0 a 1.0,
  "email_type": "question|complaint|request|spam|newsletter|auto_reply|other",
  "urgency": "high|medium|low",
  "reason": "Explicação clara da decisão",
  "suggested_response": {
    "subject": "Assunto da resposta",
    "body": "Corpo da resposta em português brasileiro",
    "tone": "formal|informal|friendly|professional"
  } // apenas se decision="respond"
}

DIRETRIZES PARA RESPOSTAS:
- Use português brasileiro correto
- Mantenha tom profissional mas amigável
- Seja claro e objetivo
- Inclua próximos passos quando aplicável
- Sempre assine como "Equipe Biofraga"
"""
```

### Implementação do Serviço Gemini
```python
# gemini_service.py
from google import genai
from typing import Dict, Any
import json

class GeminiService:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        
    async def analyze_email(
        self, 
        email_data: Dict[str, Any], 
        system_prompt: str
    ) -> Dict[str, Any]:
        """
        Analisa um e-mail e retorna decisão de resposta
        """
        user_prompt = f"""
        Analise o seguinte e-mail:
        
        De: {email_data['from']}
        Para: {email_data['to']}
        Assunto: {email_data['subject']}
        
        Corpo do e-mail:
        {email_data['body']}
        
        Metadados:
        - Recebido em: {email_data['received_at']}
        - Thread ID: {email_data.get('thread_id', 'Nova conversa')}
        - Prioridade: {email_data.get('metadata', {}).get('priority', 'normal')}
        """
        
        response = await self.client.models.generate_content_async(
            model=self.model,
            contents=[
                {"role": "system", "parts": [{"text": system_prompt}]},
                {"role": "user", "parts": [{"text": user_prompt}]}
            ],
            generation_config={
                "temperature": 0.3,  # Baixa para ser mais determinístico
                "top_p": 0.9,
                "max_output_tokens": 1000,
                "response_mime_type": "application/json"
            }
        )
        
        return json.loads(response.text)
```

## 🔒 Segurança e Autenticação

### API Key Authentication
```python
# security.py
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    if credentials.credentials != settings.API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key"
        )
    return credentials.credentials
```

### Rate Limiting
```python
# Implementar com slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/emails/process")
@limiter.limit("10/minute")  # 10 requests por minuto
async def process_email(...):
    ...
```

## 📊 Modelos de Dados Completos

### Models (Pydantic)
```python
# models/email.py
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class EmailPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NORMAL = "normal"

class EmailMetadata(BaseModel):
    priority: EmailPriority = EmailPriority.NORMAL
    labels: List[str] = []
    custom_fields: Dict[str, Any] = {}

class EmailInput(BaseModel):
    email_id: str = Field(..., description="ID único do e-mail")
    from_address: EmailStr = Field(..., alias="from")
    to_address: EmailStr = Field(..., alias="to")
    subject: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    thread_id: Optional[str] = None
    received_at: datetime
    attachments: List[str] = []
    metadata: EmailMetadata = EmailMetadata()
    
    class Config:
        json_schema_extra = {
            "example": {
                "email_id": "msg_12345",
                "from": "cliente@example.com",
                "to": "support@biofraga.com",
                "subject": "Dúvida sobre produto",
                "body": "Olá, gostaria de saber...",
                "thread_id": "thread_123",
                "received_at": "2025-01-15T10:30:00Z",
                "attachments": [],
                "metadata": {
                    "priority": "normal",
                    "labels": ["INBOX", "UNREAD"]
                }
            }
        }

# models/response.py
class DecisionType(str, Enum):
    RESPOND = "respond"
    IGNORE = "ignore"

class EmailType(str, Enum):
    QUESTION = "question"
    COMPLAINT = "complaint"
    REQUEST = "request"
    SPAM = "spam"
    NEWSLETTER = "newsletter"
    AUTO_REPLY = "auto_reply"
    OTHER = "other"

class ResponseTone(str, Enum):
    FORMAL = "formal"
    INFORMAL = "informal"
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"

class SuggestedResponse(BaseModel):
    subject: str
    body: str
    tone: ResponseTone = ResponseTone.PROFESSIONAL

class GeminiDecision(BaseModel):
    decision: DecisionType
    confidence: float = Field(ge=0.0, le=1.0)
    email_type: EmailType
    urgency: EmailPriority
    reason: str
    suggested_response: Optional[SuggestedResponse] = None
    
class EmailProcessingResult(BaseModel):
    status: str
    email_id: str
    decision: DecisionType
    confidence: float
    reason: str
    suggested_response: Optional[SuggestedResponse] = None
    processing_time: float
    processed_at: datetime
    job_id: Optional[str] = None
```

## 🗄️ Integração com Supabase

### Schema do Banco
```sql
-- Tabela de e-mails processados
CREATE TABLE processed_emails (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email_id VARCHAR(255) UNIQUE NOT NULL,
    from_address VARCHAR(255) NOT NULL,
    to_address VARCHAR(255) NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    thread_id VARCHAR(255),
    received_at TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Resultado do processamento
    decision VARCHAR(20) NOT NULL CHECK (decision IN ('respond', 'ignore')),
    confidence DECIMAL(3, 2) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    email_type VARCHAR(50) NOT NULL,
    urgency VARCHAR(20) NOT NULL,
    reason TEXT NOT NULL,
    
    -- Resposta sugerida (se aplicável)
    suggested_subject TEXT,
    suggested_body TEXT,
    suggested_tone VARCHAR(20),
    
    -- Metadados
    processing_time_seconds DECIMAL(10, 3) NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    prompt_id VARCHAR(255),
    model_version VARCHAR(50) NOT NULL,
    
    -- Índices
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX idx_processed_emails_email_id ON processed_emails(email_id);
CREATE INDEX idx_processed_emails_decision ON processed_emails(decision);
CREATE INDEX idx_processed_emails_processed_at ON processed_emails(processed_at);
CREATE INDEX idx_processed_emails_from_address ON processed_emails(from_address);

-- Tabela de prompts
CREATE TABLE ai_prompts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    system_prompt TEXT NOT NULL,
    decision_criteria JSONB NOT NULL,
    active BOOLEAN DEFAULT false,
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de analytics (agregados)
CREATE TABLE email_analytics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    date DATE NOT NULL,
    total_processed INTEGER DEFAULT 0,
    total_responded INTEGER DEFAULT 0,
    total_ignored INTEGER DEFAULT 0,
    avg_processing_time DECIMAL(10, 3),
    avg_confidence DECIMAL(3, 2),
    top_respond_reasons JSONB,
    top_ignore_reasons JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(date)
);

-- Trigger para atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_processed_emails_updated_at 
    BEFORE UPDATE ON processed_emails 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_prompts_updated_at 
    BEFORE UPDATE ON ai_prompts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

## 🚀 Roadmap de Implementação

### Fase 1: MVP Básico (3-5 dias)
1. ✅ Estrutura base do FastAPI
2. ✅ Modelos de dados
3. ✅ Integração básica com Gemini
4. ✅ Endpoint único de processamento síncrono
5. ✅ Testes básicos
6. ✅ Documentação Swagger

### Fase 2: Persistência e Analytics (3-4 dias)
1. Integração com Supabase
2. Salvar histórico de processamento
3. Endpoint de analytics básico
4. Gerenciamento de prompts
5. Logs estruturados

### Fase 3: Processamento Assíncrono (4-5 dias)
1. Adicionar Redis
2. Implementar Celery workers
3. Sistema de filas
4. Webhooks de notificação
5. Status tracking

### Fase 4: Otimizações (3-4 dias)
1. Cache de respostas similares
2. Batch processing
3. Rate limiting avançado
4. Métricas com Prometheus
5. Dashboard com Grafana

### Fase 5: Features Avançadas (5-7 dias)
1. Múltiplos modelos de IA
2. A/B testing de prompts
3. Aprendizado com feedback
4. Integração com outros LLMs
5. Auto-resposta direta via Gmail API

## 🔧 Configuração de Desenvolvimento

### Docker Compose
```yaml
version: '3.8'

services:
  backend-ai:
    build: .
    ports:
      - "8001:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    volumes:
      - ./app:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Para desenvolvimento local do Supabase (opcional)
  supabase-db:
    image: supabase/postgres:14.1.0.21
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  redis_data:
  postgres_data:
```

### Makefile para comandos comuns
```makefile
.PHONY: help install run test format lint docker-up docker-down

help:
	@echo "Comandos disponíveis:"
	@echo "  make install    - Instalar dependências"
	@echo "  make run        - Executar servidor de desenvolvimento"
	@echo "  make test       - Executar testes"
	@echo "  make format     - Formatar código com black"
	@echo "  make lint       - Verificar código com flake8"
	@echo "  make docker-up  - Subir containers Docker"
	@echo "  make docker-down - Parar containers Docker"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

run:
	uvicorn main:app --reload --port 8001

test:
	pytest tests/ -v --cov=app

format:
	black app/ tests/

lint:
	flake8 app/ tests/

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down
```

## 📝 Exemplos de Uso

### 1. Processar um e-mail simples
```bash
curl -X POST "http://localhost:8001/api/v1/emails/process" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "email_id": "msg_test_001",
    "from": "cliente@example.com",
    "to": "support@biofraga.com",
    "subject": "Quanto custa o produto X?",
    "body": "Olá, gostaria de saber o preço do produto X e se há desconto para compra em quantidade.",
    "received_at": "2025-01-15T10:30:00Z"
  }'
```

### 2. Verificar analytics
```bash
curl -X GET "http://localhost:8001/api/v1/analytics/summary?start_date=2025-01-01&end_date=2025-01-31" \
  -H "Authorization: Bearer your-api-key"
```

### 3. Atualizar system prompt
```bash
curl -X PUT "http://localhost:8001/api/v1/prompts/default" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "system_prompt": "Novo prompt mais específico...",
    "decision_criteria": {
      "respond_to": ["questions", "complaints"],
      "ignore": ["spam", "newsletters"]
    }
  }'
```

## 🎯 Considerações Finais

### Performance
- Use cache Redis para e-mails similares
- Implemente paginação em endpoints de listagem
- Use índices apropriados no banco de dados
- Configure connection pooling

### Segurança
- Sempre valide inputs com Pydantic
- Use HTTPS em produção
- Implemente rate limiting
- Logs de auditoria para todas as ações
- Criptografe dados sensíveis

### Monitoramento
- Métricas de latência por endpoint
- Taxa de sucesso/erro do Gemini
- Uso de tokens da API
- Alertas para falhas críticas

### Escalabilidade
- Design stateless para horizontal scaling
- Use filas para processos longos
- Cache distribuído com Redis
- Load balancer para múltiplas instâncias

---

**Última atualização**: Janeiro 2025  
**Autor**: Sistema XMX Email AI  
**Versão**: 1.0.0