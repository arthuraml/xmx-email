"""
Serviço para consulta de dados de rastreamento no MySQL
"""

import aiomysql
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import asyncio
from functools import wraps
from loguru import logger

from ..core.config import settings
from ..models.tracking import (
    TrackingData,
    TrackingStatus,
    TrackingCarrier,
    TrackingHistoryItem,
    TrackingQueryResult
)


def mysql_retry(max_attempts: int = 3, delay: float = 1.0):
    """
    Decorator para retry automático em caso de falha de conexão MySQL
    
    Args:
        max_attempts: Número máximo de tentativas
        delay: Delay inicial entre tentativas (cresce exponencialmente)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except (aiomysql.OperationalError, aiomysql.InterfaceError) as e:
                    error_code = e.args[0] if e.args else 0
                    # Erros de conexão perdida: 2006, 2013, 2014
                    if error_code in (2006, 2013, 2014):
                        last_exception = e
                        if attempt < max_attempts - 1:
                            wait_time = delay * (2 ** attempt)  # Backoff exponencial
                            logger.warning(
                                f"MySQL connection error (attempt {attempt + 1}/{max_attempts}): {e}. "
                                f"Retrying in {wait_time:.1f}s..."
                            )
                            await asyncio.sleep(wait_time)
                            
                            # Tenta reinicializar o pool se necessário
                            self = args[0] if args else None
                            if self and hasattr(self, '_reconnect_pool'):
                                await self._reconnect_pool()
                        else:
                            logger.error(f"MySQL connection failed after {max_attempts} attempts: {e}")
                            raise
                    else:
                        # Para outros erros, não faz retry
                        raise
                except Exception as e:
                    # Para exceções não relacionadas a conexão, não faz retry
                    logger.error(f"Unexpected error in {func.__name__}: {e}")
                    raise
            
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


class MySQLService:
    """
    Serviço para conectar e consultar banco MySQL de rastreamento
    """
    
    def __init__(self):
        self.pool: Optional[aiomysql.Pool] = None
        self._lock = asyncio.Lock()  # Para evitar múltiplas reinicializações simultâneas
        
    async def initialize(self):
        """
        Inicializa pool de conexões MySQL com configurações otimizadas
        """
        try:
            # Configurações de timeout e pool
            connect_timeout = getattr(settings, 'MYSQL_CONNECT_TIMEOUT', 10)
            read_timeout = getattr(settings, 'MYSQL_READ_TIMEOUT', 30)
            write_timeout = getattr(settings, 'MYSQL_WRITE_TIMEOUT', 30)
            pool_recycle = getattr(settings, 'MYSQL_POOL_RECYCLE', 3600)  # 1 hora
            
            self.pool = await aiomysql.create_pool(
                host=settings.MYSQL_HOST,
                port=settings.MYSQL_PORT,
                user=settings.MYSQL_USER,
                password=settings.MYSQL_PASSWORD,
                db=settings.MYSQL_DATABASE,
                minsize=1,
                maxsize=settings.MYSQL_POOL_SIZE,
                pool_recycle=pool_recycle,  # Recicla conexões antigas
                autocommit=True,
                charset='utf8mb4',
                cursorclass=aiomysql.DictCursor,
                connect_timeout=connect_timeout,
                echo=False,  # Mude para True para debug
                init_command=f"SET SESSION wait_timeout=28800, interactive_timeout=28800"  # 8 horas
            )
            logger.info(
                f"MySQL pool initialized for database: {settings.MYSQL_DATABASE} "
                f"(pool_recycle={pool_recycle}s, connect_timeout={connect_timeout}s)"
            )
            
            # Criar tabela se não existir
            await self._ensure_table_exists()
            
        except Exception as e:
            logger.error(f"Failed to initialize MySQL pool: {e}")
            raise
    
    async def _reconnect_pool(self):
        """
        Reinicializa o pool de conexões de forma segura
        """
        async with self._lock:
            logger.info("Attempting to reconnect MySQL pool...")
            try:
                # Fecha o pool antigo se existir
                if self.pool:
                    self.pool.close()
                    await self.pool.wait_closed()
                    self.pool = None
                
                # Reinicializa o pool
                await self.initialize()
                logger.info("MySQL pool reconnected successfully")
            except Exception as e:
                logger.error(f"Failed to reconnect MySQL pool: {e}")
                raise
    
    async def _ensure_connection(self):
        """
        Garante que o pool está inicializado e válido
        """
        if not self.pool:
            await self.initialize()
        elif self.pool.closed:
            await self._reconnect_pool()
    
    async def close(self):
        """
        Fecha pool de conexões
        """
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("MySQL pool closed")
    
    async def _ensure_table_exists(self):
        """
        Verifica se a tabela orders existe (não cria mais tabela nova)
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Apenas verifica se a tabela orders existe
                await cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = %s AND table_name = 'orders'
                """, (settings.MYSQL_DATABASE,))
                result = await cursor.fetchone()
                if result and result['COUNT(*)'] > 0:
                    logger.info("Orders table exists and is ready")
                else:
                    logger.warning("Orders table not found in database")
    
    @mysql_retry(max_attempts=3, delay=1.0)
    async def find_tracking_by_email(
        self,
        email: str,
        order_id: Optional[str] = None
    ) -> Optional[TrackingData]:
        """
        Busca dados de rastreamento pelo e-mail do cliente na tabela orders
        
        Args:
            email: E-mail do cliente
            order_id: ID do pedido (opcional, para busca mais específica)
            
        Returns:
            TrackingData se encontrado, None caso contrário
        """
        # Garante que o pool está válido
        await self._ensure_connection()
        
        try:
            async with self.pool.acquire() as conn:
                # Testa a conexão antes de usar (ping)
                await conn.ping()
                
                async with conn.cursor() as cursor:
                    # Prepara query para tabela orders
                    if order_id:
                        query = """
                            SELECT id, order_id_cartpanda, `order`, email_client, 
                                   tracking, purchase_date, status_id, financial_status,
                                   payment_status, country, note
                            FROM orders 
                            WHERE email_client = %s 
                            AND (order_id_cartpanda = %s OR `order` = %s)
                            AND tracking IS NOT NULL 
                            AND tracking != ''
                            ORDER BY purchase_date DESC
                            LIMIT 1
                        """
                        params = (email, order_id, order_id)
                    else:
                        query = """
                            SELECT id, order_id_cartpanda, `order`, email_client, 
                                   tracking, purchase_date, status_id, financial_status,
                                   payment_status, country, note
                            FROM orders 
                            WHERE email_client = %s
                            AND tracking IS NOT NULL 
                            AND tracking != ''
                            ORDER BY purchase_date DESC
                            LIMIT 1
                        """
                        params = (email,)
                    
                    await cursor.execute(query, params)
                    result = await cursor.fetchone()
                    
                    if result:
                        return self._parse_tracking_data_from_orders(result)
                    
                    return None
                    
        except Exception as e:
            logger.error(f"Error querying tracking data: {e}")
            raise
    
    @mysql_retry(max_attempts=3, delay=1.0)
    async def find_all_trackings_by_email(
        self,
        email: str,
        limit: int = 5
    ) -> List[TrackingData]:
        """
        Busca todos os rastreamentos de um cliente na tabela orders
        
        Args:
            email: E-mail do cliente
            limit: Limite de resultados (padrão: 5)
            
        Returns:
            Lista de TrackingData
        """
        # Garante que o pool está válido
        await self._ensure_connection()
        
        try:
            async with self.pool.acquire() as conn:
                # Testa a conexão antes de usar (ping)
                await conn.ping()
                
                async with conn.cursor() as cursor:
                    query = """
                        SELECT id, order_id_cartpanda, `order`, email_client, 
                               tracking, purchase_date, status_id, financial_status,
                               payment_status, country, note
                        FROM orders 
                        WHERE email_client = %s
                        AND tracking IS NOT NULL 
                        AND tracking != ''
                        ORDER BY purchase_date DESC
                        LIMIT %s
                    """
                    
                    await cursor.execute(query, (email, limit))
                    results = await cursor.fetchall()
                    
                    return [self._parse_tracking_data_from_orders(row) for row in results]
                    
        except Exception as e:
            logger.error(f"Error querying multiple trackings: {e}")
            return []
    
    async def insert_tracking_data(
        self,
        tracking_data: Dict[str, Any]
    ) -> bool:
        """
        Método deprecado - mantido apenas para compatibilidade
        A tabela orders já contém os dados de rastreamento
        
        Args:
            tracking_data: Dados de rastreamento
            
        Returns:
            False sempre (não insere mais dados)
        """
        logger.warning("insert_tracking_data is deprecated - orders table already contains tracking data")
        return False
    
    def _parse_tracking_data_from_orders(self, row: Dict[str, Any]) -> TrackingData:
        """
        Converte resultado da tabela orders em TrackingData
        
        Args:
            row: Linha do resultado MySQL da tabela orders
            
        Returns:
            TrackingData object
        """
        # Determina o status baseado nos campos disponíveis
        status = TrackingStatus.EM_TRANSITO  # Status padrão
        if row.get('status_id'):
            status_map = {
                'delivered': TrackingStatus.ENTREGUE,
                'shipped': TrackingStatus.EM_TRANSITO,
                'processing': TrackingStatus.POSTADO,
                'pending': TrackingStatus.POSTADO
            }
            status_id_lower = str(row['status_id']).lower()
            for key, value in status_map.items():
                if key in status_id_lower:
                    status = value
                    break
        
        # Determina a transportadora baseado no formato do código de rastreamento
        carrier = TrackingCarrier.OUTRO
        tracking_code = row.get('tracking', '')
        if tracking_code:
            if tracking_code.startswith('BR') and tracking_code.endswith('BR'):
                carrier = TrackingCarrier.CORREIOS
            elif tracking_code.startswith('94001'):
                carrier = TrackingCarrier.OUTRO  # USPS
            elif len(tracking_code) == 12 and tracking_code.isdigit():
                carrier = TrackingCarrier.MERCADO_ENVIOS
        
        # Cria histórico simplificado baseado na data de compra
        history = []
        if row.get('purchase_date'):
            history.append(TrackingHistoryItem(
                date=row['purchase_date'],
                status='Pedido processado',
                location=row.get('country', 'Brasil'),
                description=f"Pedido {row.get('order_id_cartpanda', '')} processado"
            ))
        
        return TrackingData(
            order_id=row.get('order_id_cartpanda', row.get('order', '')),
            tracking_code=tracking_code,
            carrier=carrier,
            status=status,
            last_update=row.get('purchase_date', datetime.now()),
            last_location=row.get('country', 'Brasil'),
            estimated_delivery=None,  # Não disponível na tabela orders
            delivered_at=None,
            history=history,
            recipient_name=None,  # Não disponível na tabela orders
            recipient_document=None,
            delivery_address=None,
            source='mysql_orders',
            confidence=1.0
        )
    
    def _parse_tracking_data(self, row: Dict[str, Any]) -> TrackingData:
        """
        Converte resultado do banco em TrackingData
        
        Args:
            row: Linha do resultado MySQL
            
        Returns:
            TrackingData object
        """
        # Parse histórico JSON
        history = []
        if row.get('tracking_json'):
            try:
                history_data = json.loads(row['tracking_json'])
                for item in history_data:
                    history.append(TrackingHistoryItem(
                        date=datetime.fromisoformat(item['date']) if isinstance(item['date'], str) else item['date'],
                        status=item.get('status', ''),
                        location=item.get('location'),
                        description=item.get('description')
                    ))
            except Exception as e:
                logger.warning(f"Failed to parse tracking history: {e}")
        
        # Mapeia status do banco para enum
        status = TrackingStatus.NAO_ENCONTRADO
        if row.get('status'):
            try:
                status = TrackingStatus(row['status'])
            except ValueError:
                logger.warning(f"Unknown tracking status: {row['status']}")
        
        # Mapeia transportadora
        carrier = TrackingCarrier.OUTRO
        if row.get('carrier'):
            try:
                carrier = TrackingCarrier(row['carrier'])
            except ValueError:
                # Tenta encontrar por nome similar
                carrier_map = {
                    'correios': TrackingCarrier.CORREIOS,
                    'mercado': TrackingCarrier.MERCADO_ENVIOS,
                    'loggi': TrackingCarrier.LOGGI,
                    'total': TrackingCarrier.TOTAL_EXPRESS,
                    'jadlog': TrackingCarrier.JADLOG,
                    'sequoia': TrackingCarrier.SEQUOIA
                }
                carrier_lower = row['carrier'].lower()
                for key, value in carrier_map.items():
                    if key in carrier_lower:
                        carrier = value
                        break
        
        return TrackingData(
            order_id=row['order_id'],
            tracking_code=row['tracking_code'] or '',
            carrier=carrier,
            status=status,
            last_update=row['last_update'] or datetime.now(),
            last_location=row.get('last_location'),
            estimated_delivery=row.get('estimated_delivery'),
            delivered_at=row.get('delivered_at'),
            history=history,
            recipient_name=row.get('recipient_name'),
            recipient_document=row.get('recipient_document'),
            delivery_address=row.get('delivery_address'),
            source='mysql',
            confidence=1.0
        )
    
    async def query_tracking(
        self,
        email_id: str,
        sender_email: str,
        order_id: Optional[str] = None
    ) -> TrackingQueryResult:
        """
        Consulta rastreamento e retorna resultado formatado
        
        Args:
            email_id: ID do e-mail para referência
            sender_email: E-mail do remetente
            order_id: ID do pedido (opcional)
            
        Returns:
            TrackingQueryResult com dados ou indicação de não encontrado
        """
        import time
        start_time = time.time()
        
        try:
            tracking_data = await self.find_tracking_by_email(sender_email, order_id)
            query_time_ms = int((time.time() - start_time) * 1000)
            
            if tracking_data:
                return TrackingQueryResult(
                    email_id=email_id,
                    found=True,
                    tracking_data=tracking_data,
                    query_time_ms=query_time_ms,
                    data_source='mysql',
                    saved_to_db=False  # Será salvo pelo endpoint
                )
            else:
                # Não encontrado, retorna sugestões
                suggestions = [
                    "Verifique se o e-mail está correto",
                    "O pedido pode estar em processamento",
                    "Entre em contato com o suporte para mais informações"
                ]
                
                return TrackingQueryResult(
                    email_id=email_id,
                    found=False,
                    tracking_data=None,
                    query_time_ms=query_time_ms,
                    data_source='mysql',
                    suggestions=suggestions,
                    saved_to_db=False
                )
                
        except Exception as e:
            logger.error(f"Error in query_tracking: {e}")
            query_time_ms = int((time.time() - start_time) * 1000)
            
            return TrackingQueryResult(
                email_id=email_id,
                found=False,
                tracking_data=None,
                query_time_ms=query_time_ms,
                data_source='mysql',
                error=str(e),
                saved_to_db=False
            )
    
    @mysql_retry(max_attempts=2, delay=0.5)
    async def test_connection(self) -> bool:
        """
        Testa conexão com MySQL
        
        Returns:
            True se conectou com sucesso
        """
        try:
            await self._ensure_connection()
            
            async with self.pool.acquire() as conn:
                # Faz ping na conexão
                await conn.ping()
                
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1")
                    result = await cursor.fetchone()
                    return result is not None
                    
        except Exception as e:
            logger.error(f"MySQL connection test failed: {e}")
            return False


# Instância singleton do serviço
mysql_service = MySQLService()