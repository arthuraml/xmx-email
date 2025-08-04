"""
Cliente Supabase para o backend AI
"""

from supabase import create_client, Client
from typing import Optional
from loguru import logger

from ..core.config import settings

# Cliente global do Supabase
supabase_client: Optional[Client] = None


async def init_supabase() -> Client:
    """
    Inicializa o cliente Supabase
    """
    global supabase_client
    
    try:
        supabase_client = create_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_KEY
        )
        
        logger.info("Cliente Supabase inicializado com sucesso")
        return supabase_client
        
    except Exception as e:
        logger.error(f"Erro ao inicializar cliente Supabase: {e}")
        raise


def get_supabase() -> Client:
    """
    Retorna o cliente Supabase ou inicializa se necessário
    """
    global supabase_client
    
    if supabase_client is None:
        raise RuntimeError("Cliente Supabase não foi inicializado. Chame init_supabase() primeiro.")
    
    return supabase_client


async def test_supabase_connection() -> bool:
    """
    Testa a conexão com Supabase
    """
    try:
        client = get_supabase()
        
        # Tenta fazer uma query simples
        result = await client.table('processed_emails').select('count').limit(1).execute()
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao testar conexão com Supabase: {e}")
        return False


# Funções auxiliares para operações comuns
async def save_processed_email(email_data: dict) -> dict:
    """
    Salva um e-mail processado no banco
    """
    try:
        client = get_supabase()
        
        result = await client.table('processed_emails').insert(email_data).execute()
        
        return result.data[0] if result.data else None
        
    except Exception as e:
        logger.error(f"Erro ao salvar e-mail processado: {e}")
        raise


async def get_processed_email(email_id: str) -> Optional[dict]:
    """
    Busca um e-mail processado pelo ID
    """
    try:
        client = get_supabase()
        
        result = await client.table('processed_emails').select('*').eq('email_id', email_id).single().execute()
        
        return result.data
        
    except Exception as e:
        logger.error(f"Erro ao buscar e-mail processado: {e}")
        return None


async def update_email_analytics(date_str: str, metrics: dict) -> dict:
    """
    Atualiza analytics de e-mails
    """
    try:
        client = get_supabase()
        
        # Tenta fazer upsert (insert ou update)
        result = await client.table('email_analytics').upsert({
            'date': date_str,
            **metrics
        }).execute()
        
        return result.data[0] if result.data else None
        
    except Exception as e:
        logger.error(f"Erro ao atualizar analytics: {e}")
        raise