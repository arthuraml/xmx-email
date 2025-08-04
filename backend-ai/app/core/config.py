"""
Configurações da aplicação
"""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    Configurações do backend AI
    """
    # Application Settings
    APP_NAME: str = "XMX Email AI Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    API_KEY: str
    API_PREFIX: str = "/api/v1"
    
    # Google Gemini Configuration
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_TEMPERATURE: float = 0.3
    GEMINI_MAX_OUTPUT_TOKENS: int = 1000
    GEMINI_TOP_P: float = 0.9
    
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str  # Service role key for backend
    
    # Redis Configuration (for future async processing)
    REDIS_URL: Optional[str] = "redis://localhost:6379"
    REDIS_DB: int = 0
    
    # CORS Settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 10
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Processing Settings
    MAX_CONCURRENT_REQUESTS: int = 10
    PROCESSING_TIMEOUT: int = 30  # seconds
    ENABLE_RESPONSE_CACHE: bool = True
    CACHE_TTL: int = 300  # seconds
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Email Processing Defaults
    DEFAULT_RESPONSE_LANGUAGE: str = "pt-BR"
    DEFAULT_RESPONSE_TONE: str = "professional"
    AUTO_RESPOND_ENABLED: bool = False
    
    # Monitoring (optional)
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    # Default System Prompt
    DEFAULT_SYSTEM_PROMPT: str = """
Você é um assistente inteligente de e-mail para a empresa Biofraga.
Sua função é analisar e-mails recebidos e decidir se devem ser respondidos.

CONTEXTO DA EMPRESA:
- Nome: Biofraga
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
    
    model_config = SettingsConfigDict(
        env_file="../.env",  # Busca o .env na raiz do projeto
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignora variáveis extras no .env
    )
    
    def get_cors_origins(self) -> List[str]:
        """
        Retorna origens CORS como lista
        """
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS
    
    def get_database_url(self) -> str:
        """
        Constrói a URL do banco de dados para SQLAlchemy (se necessário)
        """
        # Por enquanto, usamos apenas Supabase
        # Mas isso pode ser útil para conexão direta com PostgreSQL
        return f"{self.SUPABASE_URL}/rest/v1"
    
    @property
    def is_production(self) -> bool:
        """
        Verifica se está em produção
        """
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """
        Verifica se está em desenvolvimento
        """
        return self.ENVIRONMENT.lower() == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna instância singleton das configurações
    """
    return Settings()


# Instância global das configurações
settings = get_settings()