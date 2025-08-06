"""
Serviço para consulta de dados de rastreamento no MySQL
"""

import aiomysql
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
from loguru import logger

from ..core.config import settings
from ..models.tracking import (
    TrackingData,
    TrackingStatus,
    TrackingCarrier,
    TrackingHistoryItem,
    TrackingQueryResult
)


class MySQLService:
    """
    Serviço para conectar e consultar banco MySQL de rastreamento
    """
    
    def __init__(self):
        self.pool: Optional[aiomysql.Pool] = None
        
    async def initialize(self):
        """
        Inicializa pool de conexões MySQL
        """
        try:
            self.pool = await aiomysql.create_pool(
                host=settings.MYSQL_HOST,
                port=settings.MYSQL_PORT,
                user=settings.MYSQL_USER,
                password=settings.MYSQL_PASSWORD,
                db=settings.MYSQL_DATABASE,
                minsize=1,
                maxsize=settings.MYSQL_POOL_SIZE,
                autocommit=True,
                charset='utf8mb4',
                cursorclass=aiomysql.DictCursor
            )
            logger.info(f"MySQL pool initialized for database: {settings.MYSQL_DATABASE}")
            
            # Criar tabela se não existir
            await self._ensure_table_exists()
            
        except Exception as e:
            logger.error(f"Failed to initialize MySQL pool: {e}")
            raise
    
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
        Garante que a tabela de rastreamento existe
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tracking_orders (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        customer_email VARCHAR(255) NOT NULL,
                        order_id VARCHAR(100) NOT NULL,
                        tracking_code VARCHAR(100),
                        carrier VARCHAR(50),
                        status VARCHAR(50),
                        last_location VARCHAR(255),
                        last_update DATETIME,
                        estimated_delivery DATETIME,
                        delivered_at DATETIME,
                        recipient_name VARCHAR(255),
                        recipient_document VARCHAR(50),
                        delivery_address TEXT,
                        tracking_json TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX idx_email (customer_email),
                        INDEX idx_order (order_id),
                        INDEX idx_tracking (tracking_code),
                        INDEX idx_status (status)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                logger.info("Tracking orders table verified/created")
    
    async def find_tracking_by_email(
        self,
        email: str,
        order_id: Optional[str] = None
    ) -> Optional[TrackingData]:
        """
        Busca dados de rastreamento pelo e-mail do cliente
        
        Args:
            email: E-mail do cliente
            order_id: ID do pedido (opcional, para busca mais específica)
            
        Returns:
            TrackingData se encontrado, None caso contrário
        """
        if not self.pool:
            await self.initialize()
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Prepara query
                    if order_id:
                        query = """
                            SELECT * FROM tracking_orders 
                            WHERE customer_email = %s AND order_id = %s
                            ORDER BY last_update DESC
                            LIMIT 1
                        """
                        params = (email, order_id)
                    else:
                        query = """
                            SELECT * FROM tracking_orders 
                            WHERE customer_email = %s
                            ORDER BY last_update DESC
                            LIMIT 1
                        """
                        params = (email,)
                    
                    await cursor.execute(query, params)
                    result = await cursor.fetchone()
                    
                    if result:
                        return self._parse_tracking_data(result)
                    
                    return None
                    
        except Exception as e:
            logger.error(f"Error querying tracking data: {e}")
            raise
    
    async def find_all_trackings_by_email(
        self,
        email: str,
        limit: int = 10
    ) -> List[TrackingData]:
        """
        Busca todos os rastreamentos de um cliente
        
        Args:
            email: E-mail do cliente
            limit: Limite de resultados
            
        Returns:
            Lista de TrackingData
        """
        if not self.pool:
            await self.initialize()
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    query = """
                        SELECT * FROM tracking_orders 
                        WHERE customer_email = %s
                        ORDER BY last_update DESC
                        LIMIT %s
                    """
                    
                    await cursor.execute(query, (email, limit))
                    results = await cursor.fetchall()
                    
                    return [self._parse_tracking_data(row) for row in results]
                    
        except Exception as e:
            logger.error(f"Error querying multiple trackings: {e}")
            return []
    
    async def insert_tracking_data(
        self,
        tracking_data: Dict[str, Any]
    ) -> bool:
        """
        Insere dados de rastreamento no banco (para testes)
        
        Args:
            tracking_data: Dados de rastreamento
            
        Returns:
            True se inserido com sucesso
        """
        if not self.pool:
            await self.initialize()
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    query = """
                        INSERT INTO tracking_orders (
                            customer_email, order_id, tracking_code, carrier,
                            status, last_location, last_update, estimated_delivery,
                            recipient_name, delivery_address, tracking_json
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            status = VALUES(status),
                            last_location = VALUES(last_location),
                            last_update = VALUES(last_update),
                            tracking_json = VALUES(tracking_json)
                    """
                    
                    # Prepara dados
                    tracking_json = json.dumps(
                        tracking_data.get('history', []),
                        default=str
                    )
                    
                    params = (
                        tracking_data.get('customer_email'),
                        tracking_data.get('order_id'),
                        tracking_data.get('tracking_code'),
                        tracking_data.get('carrier'),
                        tracking_data.get('status'),
                        tracking_data.get('last_location'),
                        tracking_data.get('last_update'),
                        tracking_data.get('estimated_delivery'),
                        tracking_data.get('recipient_name'),
                        tracking_data.get('delivery_address'),
                        tracking_json
                    )
                    
                    await cursor.execute(query, params)
                    logger.info(f"Tracking data inserted/updated for order {tracking_data.get('order_id')}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error inserting tracking data: {e}")
            return False
    
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
    
    async def test_connection(self) -> bool:
        """
        Testa conexão com MySQL
        
        Returns:
            True se conectou com sucesso
        """
        try:
            if not self.pool:
                await self.initialize()
            
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1")
                    result = await cursor.fetchone()
                    return result is not None
                    
        except Exception as e:
            logger.error(f"MySQL connection test failed: {e}")
            return False


# Instância singleton do serviço
mysql_service = MySQLService()