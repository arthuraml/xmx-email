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
    
    # MySQL Configuration
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str = "xmx_tracking"
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str
    MYSQL_POOL_SIZE: int = 5
    MYSQL_POOL_MAX_OVERFLOW: int = 10
    
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