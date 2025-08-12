#!/usr/bin/env python3
"""
Script de teste para validar o novo fluxo de processamento
"""

import asyncio
import json
from datetime import datetime
from app.models.email import EmailInput
from app.models.processing import EmailProcessingResponse
from app.services.processing_service import processing_service
from app.services.mysql_service import mysql_service
from loguru import logger

# Configurar logger para teste
logger.add("test_flow.log", rotation="1 MB")


async def test_classification_only():
    """Testa e-mail que é apenas suporte (não rastreamento)"""
    print("\n=== Teste 1: Classificação apenas (suporte) ===")
    
    email = EmailInput(
        email_id="test_001",
        from_address="cliente@example.com",
        to_address="support@biofraga.com",
        subject="Dúvida sobre produto",
        body="Gostaria de saber mais informações sobre o produto X. Ele tem garantia?",
        received_at=datetime.utcnow()
    )
    
    result = await processing_service.process_email(email)
    
    print(f"Email ID: {result.email_id}")
    print(f"É suporte: {result.classification.is_support}")
    print(f"É rastreamento: {result.classification.is_tracking}")
    print(f"Confiança: {result.classification.confidence:.2f}")
    print(f"Tokens usados: {result.tokens.total_tokens}")
    
    return result


async def test_tracking_request():
    """Testa e-mail que solicita rastreamento"""
    print("\n=== Teste 2: Solicitação de rastreamento ===")
    
    email = EmailInput(
        email_id="test_002",
        from_address="matheuspizarromarques@gmail.com",  # Email real do banco
        to_address="support@biofraga.com",
        subject="Onde está meu pedido?",
        body="Olá, gostaria de saber o status do meu pedido. Já faz uma semana que comprei.",
        received_at=datetime.utcnow()
    )
    
    result = await processing_service.process_email(email)
    
    print(f"Email ID: {result.email_id}")
    print(f"É suporte: {result.classification.is_support}")
    print(f"É rastreamento: {result.classification.is_tracking}")
    print(f"Confiança: {result.classification.confidence:.2f}")
    
    if result.tracking_data:
        print(f"Rastreamento encontrado: {result.tracking_data.found}")
        if result.tracking_data.found:
            print(f"Pedidos encontrados: {len(result.tracking_data.orders)}")
            for order in result.tracking_data.orders[:2]:
                print(f"  - Pedido: {order.order_id}")
                print(f"    Código: {order.tracking_code}")
                print(f"    Data: {order.purchase_date}")
    
    print(f"Tokens usados: {result.tokens.total_tokens}")
    
    return result


async def test_tracking_with_order_id():
    """Testa e-mail com número de pedido específico"""
    print("\n=== Teste 3: Rastreamento com número de pedido ===")
    
    email = EmailInput(
        email_id="test_003",
        from_address="cliente@example.com",
        to_address="support@biofraga.com",
        subject="Status do pedido 38495799",
        body="Olá, quero saber onde está o pedido 38495799 que fiz semana passada.",
        received_at=datetime.utcnow()
    )
    
    result = await processing_service.process_email(email)
    
    print(f"Email ID: {result.email_id}")
    print(f"É suporte: {result.classification.is_support}")
    print(f"É rastreamento: {result.classification.is_tracking}")
    print(f"Order ID extraído: {result.classification.extracted_order_id}")
    print(f"Confiança: {result.classification.confidence:.2f}")
    
    if result.tracking_data:
        print(f"Rastreamento encontrado: {result.tracking_data.found}")
    
    print(f"Tokens usados: {result.tokens.total_tokens}")
    
    return result


async def test_mysql_connection():
    """Testa conexão direta com MySQL"""
    print("\n=== Teste 4: Conexão MySQL ===")
    
    is_connected = await mysql_service.test_connection()
    print(f"MySQL conectado: {is_connected}")
    
    if is_connected:
        # Testa busca direta
        tracking = await mysql_service.find_tracking_by_email(
            email="matheuspizarromarques@gmail.com"
        )
        if tracking:
            print(f"Pedido encontrado: {tracking.order_id}")
            print(f"Código de rastreamento: {tracking.tracking_code}")
        else:
            print("Nenhum pedido encontrado para este email")
    
    return is_connected


async def main():
    """Executa todos os testes"""
    print("=" * 60)
    print("TESTE DO NOVO FLUXO DE PROCESSAMENTO")
    print("=" * 60)
    
    try:
        # Inicializa MySQL
        await mysql_service.initialize()
        
        # Executa testes
        await test_mysql_connection()
        await test_classification_only()
        await test_tracking_request()
        await test_tracking_with_order_id()
        
        print("\n" + "=" * 60)
        print("TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERRO NOS TESTES: {e}")
        logger.error(f"Erro durante testes: {e}")
    
    finally:
        # Fecha conexão MySQL
        await mysql_service.close()


if __name__ == "__main__":
    # Executa testes
    asyncio.run(main())