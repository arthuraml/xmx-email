"""
Serviço de conversão de moeda USD para BRL
Usa cache para evitar chamadas excessivas à API
"""

import httpx
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from loguru import logger


class CurrencyService:
    """
    Serviço para conversão de moeda USD para BRL em tempo real
    """
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_duration = timedelta(hours=1)  # Cache por 1 hora
        self._fallback_rate = 5.50  # Taxa de fallback caso API falhe
        
        # APIs de câmbio gratuitas (em ordem de preferência)
        self._api_endpoints = [
            {
                "name": "exchangerate-api",
                "url": "https://api.exchangerate-api.com/v4/latest/USD",
                "parser": self._parse_exchangerate_api
            },
            {
                "name": "fixer.io (free tier)",
                "url": "https://api.fixer.io/latest?base=USD&symbols=BRL",
                "parser": self._parse_fixer
            },
            {
                "name": "currencyapi",
                "url": "https://api.currencyapi.com/v3/latest?base_currency=USD&currencies=BRL",
                "parser": self._parse_currencyapi
            }
        ]
    
    def _parse_exchangerate_api(self, data: dict) -> Optional[float]:
        """Parser para exchangerate-api.com"""
        try:
            return float(data.get("rates", {}).get("BRL", 0))
        except:
            return None
    
    def _parse_fixer(self, data: dict) -> Optional[float]:
        """Parser para fixer.io"""
        try:
            return float(data.get("rates", {}).get("BRL", 0))
        except:
            return None
    
    def _parse_currencyapi(self, data: dict) -> Optional[float]:
        """Parser para currencyapi.com"""
        try:
            return float(data.get("data", {}).get("BRL", {}).get("value", 0))
        except:
            return None
    
    async def get_exchange_rate(self, force_refresh: bool = False) -> float:
        """
        Obtém a taxa de câmbio USD/BRL atual
        
        Args:
            force_refresh: Força atualização ignorando cache
        
        Returns:
            Taxa de câmbio USD/BRL (ex: 5.50 significa 1 USD = 5.50 BRL)
        """
        # Verifica cache primeiro
        if not force_refresh and self._is_cache_valid():
            logger.debug(f"Using cached exchange rate: {self._cache['rate']}")
            return self._cache["rate"]
        
        # Tenta obter taxa de cada API
        async with httpx.AsyncClient(timeout=10.0) as client:
            for endpoint in self._api_endpoints:
                try:
                    logger.info(f"Fetching exchange rate from {endpoint['name']}")
                    response = await client.get(endpoint["url"])
                    
                    if response.status_code == 200:
                        data = response.json()
                        rate = endpoint["parser"](data)
                        
                        if rate and rate > 0:
                            # Atualiza cache
                            self._cache = {
                                "rate": rate,
                                "timestamp": datetime.now(),
                                "source": endpoint["name"]
                            }
                            logger.info(f"Exchange rate updated: 1 USD = {rate:.2f} BRL (source: {endpoint['name']})")
                            return rate
                            
                except Exception as e:
                    logger.warning(f"Failed to fetch from {endpoint['name']}: {e}")
                    continue
        
        # Se todas as APIs falharem, usa fallback
        logger.warning(f"All currency APIs failed, using fallback rate: {self._fallback_rate}")
        
        # Atualiza cache com fallback
        self._cache = {
            "rate": self._fallback_rate,
            "timestamp": datetime.now(),
            "source": "fallback"
        }
        
        return self._fallback_rate
    
    def _is_cache_valid(self) -> bool:
        """Verifica se o cache ainda é válido"""
        if not self._cache:
            return False
        
        cache_age = datetime.now() - self._cache.get("timestamp", datetime.min)
        return cache_age < self._cache_duration
    
    def convert_usd_to_brl(self, amount_usd: float, exchange_rate: float) -> float:
        """
        Converte valor de USD para BRL
        
        Args:
            amount_usd: Valor em USD
            exchange_rate: Taxa de câmbio USD/BRL
        
        Returns:
            Valor convertido em BRL
        """
        return amount_usd * exchange_rate
    
    async def convert_with_current_rate(self, amount_usd: float) -> Dict[str, Any]:
        """
        Converte USD para BRL usando a taxa atual
        
        Args:
            amount_usd: Valor em USD
        
        Returns:
            Dicionário com valor em BRL, taxa usada e fonte
        """
        rate = await self.get_exchange_rate()
        amount_brl = self.convert_usd_to_brl(amount_usd, rate)
        
        return {
            "amount_usd": amount_usd,
            "amount_brl": amount_brl,
            "exchange_rate": rate,
            "source": self._cache.get("source", "unknown"),
            "timestamp": self._cache.get("timestamp", datetime.now()).isoformat()
        }
    
    def get_cached_rate(self) -> Optional[float]:
        """
        Retorna a taxa em cache sem fazer nova requisição
        
        Returns:
            Taxa de câmbio em cache ou None se não houver cache válido
        """
        if self._is_cache_valid():
            return self._cache.get("rate")
        return None
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o cache atual
        
        Returns:
            Informações do cache incluindo taxa, fonte e timestamp
        """
        if not self._cache:
            return {
                "has_cache": False,
                "rate": None,
                "source": None,
                "timestamp": None
            }
        
        return {
            "has_cache": True,
            "rate": self._cache.get("rate"),
            "source": self._cache.get("source"),
            "timestamp": self._cache.get("timestamp").isoformat() if self._cache.get("timestamp") else None,
            "is_valid": self._is_cache_valid()
        }


# Instância singleton do serviço
currency_service = CurrencyService()


# Funções de conveniência
async def get_current_exchange_rate() -> float:
    """Obtém a taxa de câmbio atual USD/BRL"""
    return await currency_service.get_exchange_rate()


async def convert_usd_to_brl(amount_usd: float) -> Dict[str, Any]:
    """Converte USD para BRL com a taxa atual"""
    return await currency_service.convert_with_current_rate(amount_usd)


# Teste do serviço
if __name__ == "__main__":
    async def test():
        # Testa obtenção da taxa
        rate = await get_current_exchange_rate()
        print(f"Taxa atual: 1 USD = {rate:.2f} BRL")
        
        # Testa conversão
        result = await convert_usd_to_brl(100.0)
        print(f"Conversão: ${result['amount_usd']:.2f} USD = R$ {result['amount_brl']:.2f} BRL")
        print(f"Fonte: {result['source']}")
        
        # Testa cache
        cache_info = currency_service.get_cache_info()
        print(f"Cache: {cache_info}")
    
    asyncio.run(test())