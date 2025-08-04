"""
Configurações de segurança e autenticação
"""

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from loguru import logger

from .config import settings

# Security scheme
security = HTTPBearer()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """
    Verifica API Key do header Authorization
    
    Args:
        credentials: Credenciais do header
        
    Returns:
        API Key validada
        
    Raises:
        HTTPException: Se API Key inválida
    """
    api_key = credentials.credentials
    
    # Verifica se é a API Key correta
    if api_key != settings.API_KEY:
        logger.warning(f"Tentativa de acesso com API Key inválida")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return api_key


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um JWT token
    
    Args:
        data: Dados para incluir no token
        expires_delta: Tempo de expiração (opcional)
        
    Returns:
        JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verifica e decodifica um JWT token
    
    Args:
        token: JWT token
        
    Returns:
        Payload do token
        
    Raises:
        HTTPException: Se token inválido
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
        
    except JWTError as e:
        logger.error(f"Erro ao verificar token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se a senha está correta
    
    Args:
        plain_password: Senha em texto plano
        hashed_password: Hash da senha
        
    Returns:
        True se senha correta
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Gera hash de uma senha
    
    Args:
        password: Senha em texto plano
        
    Returns:
        Hash da senha
    """
    return pwd_context.hash(password)


class RateLimiter:
    """
    Rate limiter simples baseado em memória
    (Em produção, usar Redis)
    """
    
    def __init__(self):
        self.requests: Dict[str, List[datetime]] = {}
    
    def is_allowed(
        self,
        key: str,
        max_requests: int = settings.RATE_LIMIT_REQUESTS,
        window_seconds: int = settings.RATE_LIMIT_PERIOD
    ) -> bool:
        """
        Verifica se requisição é permitida
        
        Args:
            key: Chave única (IP, user_id, etc)
            max_requests: Máximo de requisições
            window_seconds: Janela de tempo em segundos
            
        Returns:
            True se permitido
        """
        now = datetime.utcnow()
        
        # Limpa requisições antigas
        if key in self.requests:
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if (now - req_time).total_seconds() < window_seconds
            ]
        else:
            self.requests[key] = []
        
        # Verifica limite
        if len(self.requests[key]) >= max_requests:
            return False
        
        # Adiciona nova requisição
        self.requests[key].append(now)
        return True
    
    def clear_old_entries(self):
        """
        Limpa entradas antigas (executar periodicamente)
        """
        now = datetime.utcnow()
        keys_to_remove = []
        
        for key, requests in self.requests.items():
            # Remove requisições antigas
            self.requests[key] = [
                req_time for req_time in requests
                if (now - req_time).total_seconds() < 300  # 5 minutos
            ]
            
            # Se não há mais requisições, marca para remoção
            if not self.requests[key]:
                keys_to_remove.append(key)
        
        # Remove chaves vazias
        for key in keys_to_remove:
            del self.requests[key]


# Instância global do rate limiter
rate_limiter = RateLimiter()