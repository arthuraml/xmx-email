#!/usr/bin/env python3
"""
Script para testar a configuração do backend
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Testa se todos os imports estão funcionando"""
    print("🧪 Testando imports...")
    
    try:
        # Core imports
        from app.core.config import settings
        print("✅ Config importado com sucesso")
        
        from app.core.gemini import init_gemini_client
        print("✅ Gemini client importado com sucesso")
        
        from app.core.security import create_access_token, verify_api_key
        print("✅ Security importado com sucesso")
        
        # Model imports
        from app.models.email import EmailInput, EmailBatch
        print("✅ Email models importados com sucesso")
        
        from app.models.response import GeminiDecision, EmailProcessingResult
        print("✅ Response models importados com sucesso")
        
        
        # API imports
        from app.api.v1 import emails_router, health_router
        print("✅ API routers importados com sucesso")
        
        # DB imports
        from app.db.supabase import init_supabase
        print("✅ Supabase client importado com sucesso")
        
        print("\n✨ Todos os imports estão funcionando!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao importar: {e}")
        return False

def test_environment():
    """Testa se as variáveis de ambiente estão configuradas"""
    print("\n🔧 Verificando variáveis de ambiente...")
    
    try:
        from app.core.config import settings
        
        # Verificar variáveis críticas
        missing = []
        
        if not settings.API_KEY or settings.API_KEY == "your-secure-api-key-here":
            missing.append("API_KEY")
        
        if not settings.SECRET_KEY or settings.SECRET_KEY == "your-secret-key-for-jwt-here":
            missing.append("SECRET_KEY")
            
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your-gemini-api-key-here":
            missing.append("GEMINI_API_KEY")
            
        if not settings.SUPABASE_KEY or settings.SUPABASE_KEY == "your-supabase-service-role-key-here":
            missing.append("SUPABASE_KEY")
        
        if missing:
            print(f"\n⚠️  Variáveis de ambiente faltando ou com valores padrão:")
            for var in missing:
                print(f"   - {var}")
            print(f"\n📝 Configure essas variáveis no arquivo .env na raiz do projeto")
            print(f"   Consulte INSTRUCOES_CHAVES_API.md para obter as chaves")
            return False
        else:
            print("✅ Todas as variáveis de ambiente estão configuradas!")
            return True
            
    except Exception as e:
        print(f"\n❌ Erro ao verificar ambiente: {e}")
        return False

def test_dependencies():
    """Testa se todas as dependências estão instaladas"""
    print("\n📦 Verificando dependências...")
    
    try:
        import fastapi
        print(f"✅ FastAPI {fastapi.__version__}")
        
        import uvicorn
        print("✅ Uvicorn instalado")
        
        import google.genai
        print("✅ Google GenAI instalado")
        
        import supabase
        print("✅ Supabase instalado")
        
        import pydantic
        print(f"✅ Pydantic {pydantic.__version__}")
        
        import loguru
        print("✅ Loguru instalado")
        
        print("\n✨ Todas as dependências estão instaladas!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Dependência faltando: {e}")
        print("\n💡 Execute: pip install -r requirements.txt")
        return False

def main():
    print("=" * 50)
    print("🚀 XMX Email AI Backend - Teste de Configuração")
    print("=" * 50)
    
    # Executar testes
    deps_ok = test_dependencies()
    imports_ok = test_imports()
    env_ok = test_environment()
    
    print("\n" + "=" * 50)
    print("📊 Resumo dos Testes:")
    print("=" * 50)
    
    print(f"Dependências: {'✅ OK' if deps_ok else '❌ FALHOU'}")
    print(f"Imports:      {'✅ OK' if imports_ok else '❌ FALHOU'}")
    print(f"Environment:  {'✅ OK' if env_ok else '❌ FALHOU'}")
    
    if deps_ok and imports_ok:
        if env_ok:
            print("\n🎉 Backend está pronto para executar!")
            print("\n💡 Para iniciar o servidor:")
            print("   python main.py")
        else:
            print("\n⚠️  Backend está configurado, mas faltam as chaves de API")
            print("   Configure as variáveis no arquivo .env primeiro")
    else:
        print("\n❌ Corrija os erros acima antes de executar o backend")
    
    return 0 if (deps_ok and imports_ok) else 1

if __name__ == "__main__":
    sys.exit(main())