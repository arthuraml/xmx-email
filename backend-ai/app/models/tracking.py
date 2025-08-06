"""
Modelos Pydantic para rastreamento de pedidos
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class TrackingStatus(str, Enum):
    """Status possíveis de rastreamento"""
    PEDIDO_CONFIRMADO = "PEDIDO_CONFIRMADO"
    COLETADO = "COLETADO"
    EM_TRANSITO = "EM_TRANSITO"
    SAIU_PARA_ENTREGA = "SAIU_PARA_ENTREGA"
    ENTREGUE = "ENTREGUE"
    TENTATIVA_ENTREGA = "TENTATIVA_ENTREGA"
    DEVOLVIDO = "DEVOLVIDO"
    EXTRAVIADO = "EXTRAVIADO"
    NAO_ENCONTRADO = "NAO_ENCONTRADO"


class TrackingCarrier(str, Enum):
    """Transportadoras disponíveis"""
    CORREIOS = "Correios"
    MERCADO_ENVIOS = "Mercado Envios"
    LOGGI = "Loggi"
    TOTAL_EXPRESS = "Total Express"
    JADLOG = "JadLog"
    SEQUOIA = "Sequoia"
    OUTRO = "Outro"


class TrackingHistoryItem(BaseModel):
    """Item do histórico de rastreamento"""
    date: datetime = Field(..., description="Data do evento")
    status: str = Field(..., description="Status do evento")
    location: Optional[str] = Field(None, description="Localização")
    description: Optional[str] = Field(None, description="Descrição adicional")


class TrackingQueryInput(BaseModel):
    """Entrada para consulta de rastreamento"""
    email_id: str = Field(..., description="ID do e-mail relacionado")
    sender_email: EmailStr = Field(..., description="E-mail do remetente para busca")
    order_id: Optional[str] = Field(None, description="ID do pedido se conhecido")
    tracking_code: Optional[str] = Field(None, description="Código de rastreamento se conhecido")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email_id": "msg_12345",
                "sender_email": "cliente@example.com",
                "order_id": "PED-2025-001",
                "tracking_code": None
            }
        }
    }


class TrackingData(BaseModel):
    """Dados de rastreamento do pedido"""
    order_id: str = Field(..., description="ID do pedido")
    tracking_code: str = Field(..., description="Código de rastreamento")
    carrier: TrackingCarrier = Field(..., description="Transportadora")
    status: TrackingStatus = Field(..., description="Status atual")
    last_update: datetime = Field(..., description="Última atualização")
    
    # Localização e previsão
    last_location: Optional[str] = Field(None, description="Última localização conhecida")
    estimated_delivery: Optional[datetime] = Field(None, description="Previsão de entrega")
    delivered_at: Optional[datetime] = Field(None, description="Data de entrega se entregue")
    
    # Histórico
    history: List[TrackingHistoryItem] = Field(default_factory=list, description="Histórico de movimentações")
    
    # Informações adicionais
    recipient_name: Optional[str] = Field(None, description="Nome do destinatário")
    recipient_document: Optional[str] = Field(None, description="CPF/CNPJ do destinatário")
    delivery_address: Optional[str] = Field(None, description="Endereço de entrega")
    
    # Metadados
    source: str = Field("mysql", description="Fonte dos dados (mysql/api/cache)")
    confidence: float = Field(1.0, description="Confiança nos dados")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "order_id": "PED-2025-001",
                "tracking_code": "BR123456789BR",
                "carrier": "Correios",
                "status": "EM_TRANSITO",
                "last_update": "2025-01-06T14:30:00Z",
                "last_location": "Porto Alegre/RS",
                "estimated_delivery": "2025-01-09T18:00:00Z",
                "history": [
                    {
                        "date": "2025-01-04T10:00:00Z",
                        "status": "Postado",
                        "location": "São Paulo/SP"
                    },
                    {
                        "date": "2025-01-05T14:00:00Z",
                        "status": "Em trânsito",
                        "location": "Curitiba/PR"
                    }
                ],
                "source": "mysql",
                "confidence": 1.0
            }
        }
    }


class TrackingQueryResult(BaseModel):
    """Resultado da consulta de rastreamento"""
    email_id: str = Field(..., description="ID do e-mail relacionado")
    found: bool = Field(..., description="Se encontrou dados de rastreamento")
    tracking_data: Optional[TrackingData] = Field(None, description="Dados de rastreamento se encontrados")
    
    # Metadados da consulta
    query_time_ms: int = Field(..., description="Tempo de consulta em ms")
    data_source: str = Field(..., description="Fonte consultada")
    
    # Status e erros
    error: Optional[str] = Field(None, description="Mensagem de erro se houver")
    suggestions: List[str] = Field(default_factory=list, description="Sugestões se não encontrado")
    
    # Salvamento
    saved_to_db: bool = Field(False, description="Se foi salvo no banco")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email_id": "msg_12345",
                "found": True,
                "tracking_data": {
                    "order_id": "PED-2025-001",
                    "tracking_code": "BR123456789BR",
                    "carrier": "Correios",
                    "status": "EM_TRANSITO",
                    "last_update": "2025-01-06T14:30:00Z",
                    "last_location": "Porto Alegre/RS"
                },
                "query_time_ms": 45,
                "data_source": "mysql",
                "saved_to_db": True
            }
        }
    }


class BatchTrackingQueryInput(BaseModel):
    """Entrada para consulta de rastreamento em lote"""
    queries: List[TrackingQueryInput] = Field(..., min_length=1, max_length=20)
    save_to_db: bool = Field(True, description="Salvar resultados no banco")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "queries": [
                    {
                        "email_id": "msg_001",
                        "sender_email": "cliente1@example.com"
                    },
                    {
                        "email_id": "msg_002",
                        "sender_email": "cliente2@example.com",
                        "order_id": "PED-2025-002"
                    }
                ],
                "save_to_db": True
            }
        }
    }


class BatchTrackingQueryResult(BaseModel):
    """Resultado da consulta de rastreamento em lote"""
    total_queries: int = Field(..., description="Total de consultas")
    found_count: int = Field(..., description="Quantidade encontrada")
    not_found_count: int = Field(..., description="Quantidade não encontrada")
    results: List[TrackingQueryResult] = Field(..., description="Resultados individuais")
    processing_time_ms: int = Field(..., description="Tempo total de processamento")
    
    @property
    def success_rate(self) -> float:
        """Calcula taxa de sucesso"""
        if self.total_queries == 0:
            return 0.0
        return self.found_count / self.total_queries