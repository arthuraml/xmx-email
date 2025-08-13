"""
Serviço de cálculo de custos para operações LLM
Integra pricing configuration e conversão de moeda
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

from .currency_service import currency_service
from ..models.processing import TokenUsage


class CostService:
    """
    Serviço para calcular custos de processamento LLM
    """
    
    def __init__(self):
        self._pricing_config: Optional[Dict[str, Any]] = None
        self._config_path = Path(__file__).parent.parent.parent / "config" / "llm_pricing.json"
        self._load_pricing_config()
    
    def _load_pricing_config(self):
        """Carrega configuração de preços do arquivo JSON"""
        try:
            if self._config_path.exists():
                with open(self._config_path, 'r') as f:
                    self._pricing_config = json.load(f)
                    logger.info(f"Pricing config loaded from {self._config_path}")
            else:
                logger.warning(f"Pricing config not found at {self._config_path}")
                # Configuração padrão de fallback
                self._pricing_config = {
                    "models": {
                        "gemini-2.5-flash": {
                            "provider": "Google",
                            "name": "Gemini 2.5 Flash",
                            "costs_usd": {
                                "input_per_million": 0.30,
                                "output_per_million": 2.50,
                                "thinking_per_million": 2.50  # Same as output
                            }
                        }
                    }
                }
        except Exception as e:
            logger.error(f"Error loading pricing config: {e}")
            # Usa configuração de fallback
            self._pricing_config = {
                "models": {
                    "gemini-2.5-flash": {
                        "costs_usd": {
                            "input_per_million": 0.30,
                            "output_per_million": 2.50,
                            "thinking_per_million": 2.50
                        }
                    }
                }
            }
    
    def get_model_pricing(self, model_name: str) -> Dict[str, float]:
        """
        Obtém os preços para um modelo específico
        
        Args:
            model_name: Nome do modelo (ex: "gemini-2.5-flash")
        
        Returns:
            Dicionário com preços por milhão de tokens
        """
        # Normaliza nome do modelo
        model_key = model_name.lower().replace("_", "-")
        
        # Mapeia variações de nomes para chave padrão
        model_mapping = {
            "gemini-2.5-flash": "gemini-2.5-flash",
            "gemini-2-5-flash": "gemini-2.5-flash",
            "gemini-2.5-flash-001": "gemini-2.5-flash",
            "gemini-2.5-flash-002": "gemini-2.5-flash",
            "gemini-2.0-flash": "gemini-2.5-flash",  # Fallback
        }
        
        model_key = model_mapping.get(model_key, model_key)
        
        if self._pricing_config and model_key in self._pricing_config.get("models", {}):
            costs = self._pricing_config["models"][model_key].get("costs_usd", {})
            
            # Garante que thinking tokens usam o mesmo preço de output
            if "thinking_per_million" not in costs and "output_per_million" in costs:
                costs["thinking_per_million"] = costs["output_per_million"]
            
            return costs
        
        # Retorna preços padrão se modelo não encontrado
        logger.warning(f"Model {model_name} not found in pricing config, using default prices")
        return {
            "input_per_million": 0.30,
            "output_per_million": 2.50,
            "thinking_per_million": 2.50
        }
    
    def calculate_token_cost_usd(
        self,
        tokens: int,
        cost_per_million: float
    ) -> float:
        """
        Calcula o custo em USD para uma quantidade de tokens
        
        Args:
            tokens: Quantidade de tokens
            cost_per_million: Custo por milhão de tokens
        
        Returns:
            Custo em USD
        """
        return (tokens / 1_000_000) * cost_per_million
    
    async def calculate_costs(
        self,
        token_usage: TokenUsage,
        model_name: str = "gemini-2.5-flash"
    ) -> Dict[str, Any]:
        """
        Calcula custos completos para um processamento
        
        Args:
            token_usage: Uso de tokens do processamento
            model_name: Nome do modelo usado
        
        Returns:
            Dicionário com custos detalhados em USD e BRL
        """
        # Obtém preços do modelo
        pricing = self.get_model_pricing(model_name)
        
        # Calcula custos em USD
        cost_input_usd = self.calculate_token_cost_usd(
            token_usage.input_tokens,
            pricing.get("input_per_million", 0.30)
        )
        
        cost_output_usd = self.calculate_token_cost_usd(
            token_usage.output_tokens,
            pricing.get("output_per_million", 2.50)
        )
        
        cost_thinking_usd = self.calculate_token_cost_usd(
            token_usage.thought_tokens,
            pricing.get("thinking_per_million", 2.50)
        )
        
        cost_total_usd = cost_input_usd + cost_output_usd + cost_thinking_usd
        
        # Obtém taxa de câmbio atual
        exchange_rate = await currency_service.get_exchange_rate()
        
        # Converte para BRL
        cost_input_brl = currency_service.convert_usd_to_brl(cost_input_usd, exchange_rate)
        cost_output_brl = currency_service.convert_usd_to_brl(cost_output_usd, exchange_rate)
        cost_thinking_brl = currency_service.convert_usd_to_brl(cost_thinking_usd, exchange_rate)
        cost_total_brl = currency_service.convert_usd_to_brl(cost_total_usd, exchange_rate)
        
        return {
            # Custos em USD
            "cost_input_usd": round(cost_input_usd, 6),
            "cost_output_usd": round(cost_output_usd, 6),
            "cost_thinking_usd": round(cost_thinking_usd, 6),
            "cost_total_usd": round(cost_total_usd, 6),
            
            # Custos em BRL
            "cost_input_brl": round(cost_input_brl, 6),
            "cost_output_brl": round(cost_output_brl, 6),
            "cost_thinking_brl": round(cost_thinking_brl, 6),
            "cost_total_brl": round(cost_total_brl, 6),
            
            # Informações adicionais
            "exchange_rate": exchange_rate,
            "model": model_name,
            "tokens": {
                "input": token_usage.input_tokens,
                "output": token_usage.output_tokens,
                "thinking": token_usage.thought_tokens,
                "total": token_usage.total_tokens
            },
            "pricing_usd_per_million": pricing,
            "calculated_at": datetime.now().isoformat()
        }
    
    async def calculate_batch_costs(
        self,
        batch_tokens: list[TokenUsage],
        model_name: str = "gemini-2.5-flash"
    ) -> Dict[str, Any]:
        """
        Calcula custos agregados para um lote de processamentos
        
        Args:
            batch_tokens: Lista de uso de tokens
            model_name: Nome do modelo usado
        
        Returns:
            Dicionário com custos agregados
        """
        # Soma todos os tokens
        total_input = sum(t.input_tokens for t in batch_tokens)
        total_output = sum(t.output_tokens for t in batch_tokens)
        total_thinking = sum(t.thought_tokens for t in batch_tokens)
        
        # Cria TokenUsage agregado
        aggregated_usage = TokenUsage(
            input_tokens=total_input,
            output_tokens=total_output,
            thought_tokens=total_thinking,
            total_tokens=total_input + total_output + total_thinking
        )
        
        # Calcula custos agregados
        costs = await self.calculate_costs(aggregated_usage, model_name)
        
        # Adiciona estatísticas
        costs["batch_size"] = len(batch_tokens)
        costs["avg_tokens_per_request"] = {
            "input": total_input / len(batch_tokens) if batch_tokens else 0,
            "output": total_output / len(batch_tokens) if batch_tokens else 0,
            "thinking": total_thinking / len(batch_tokens) if batch_tokens else 0
        }
        costs["avg_cost_per_request"] = {
            "usd": costs["cost_total_usd"] / len(batch_tokens) if batch_tokens else 0,
            "brl": costs["cost_total_brl"] / len(batch_tokens) if batch_tokens else 0
        }
        
        return costs
    
    def get_pricing_info(self) -> Dict[str, Any]:
        """
        Retorna informações completas sobre pricing
        
        Returns:
            Configuração de pricing atual
        """
        return self._pricing_config or {}
    
    async def estimate_cost(
        self,
        estimated_input_tokens: int,
        estimated_output_tokens: int,
        model_name: str = "gemini-2.5-flash"
    ) -> Dict[str, Any]:
        """
        Estima custos para um processamento futuro
        
        Args:
            estimated_input_tokens: Tokens de entrada estimados
            estimated_output_tokens: Tokens de saída estimados
            model_name: Nome do modelo
        
        Returns:
            Estimativa de custos
        """
        token_usage = TokenUsage(
            input_tokens=estimated_input_tokens,
            output_tokens=estimated_output_tokens,
            thought_tokens=0,  # Difícil estimar thinking tokens
            total_tokens=estimated_input_tokens + estimated_output_tokens
        )
        
        costs = await self.calculate_costs(token_usage, model_name)
        costs["is_estimate"] = True
        costs["note"] = "Thinking tokens not included in estimate"
        
        return costs


# Instância singleton do serviço
cost_service = CostService()


# Funções de conveniência
async def calculate_llm_costs(
    token_usage: TokenUsage,
    model_name: str = "gemini-2.5-flash"
) -> Dict[str, Any]:
    """Calcula custos para um processamento LLM"""
    return await cost_service.calculate_costs(token_usage, model_name)


async def estimate_llm_cost(
    input_tokens: int,
    output_tokens: int,
    model_name: str = "gemini-2.5-flash"
) -> Dict[str, Any]:
    """Estima custos para um processamento futuro"""
    return await cost_service.estimate_cost(input_tokens, output_tokens, model_name)


# Teste do serviço
if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Testa cálculo de custos
        usage = TokenUsage(
            input_tokens=1500,
            output_tokens=2000,
            thought_tokens=500,
            total_tokens=4000
        )
        
        costs = await calculate_llm_costs(usage)
        print("Custos calculados:")
        print(f"  Input: ${costs['cost_input_usd']:.6f} USD / R$ {costs['cost_input_brl']:.6f} BRL")
        print(f"  Output: ${costs['cost_output_usd']:.6f} USD / R$ {costs['cost_output_brl']:.6f} BRL")
        print(f"  Thinking: ${costs['cost_thinking_usd']:.6f} USD / R$ {costs['cost_thinking_brl']:.6f} BRL")
        print(f"  TOTAL: ${costs['cost_total_usd']:.6f} USD / R$ {costs['cost_total_brl']:.6f} BRL")
        print(f"  Taxa de câmbio: 1 USD = {costs['exchange_rate']:.2f} BRL")
        
        # Testa estimativa
        estimate = await estimate_llm_cost(5000, 3000)
        print(f"\nEstimativa para 5000 input + 3000 output tokens:")
        print(f"  ${estimate['cost_total_usd']:.6f} USD / R$ {estimate['cost_total_brl']:.6f} BRL")
    
    asyncio.run(test())