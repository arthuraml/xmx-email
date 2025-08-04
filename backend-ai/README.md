# XMX Email AI Backend - FastAPI + Google Gemini

Backend inteligente para processamento de e-mails usando Google Gemini AI.

## 🚀 Início Rápido

### 1. Configurar ambiente

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente (Linux/Mac)
source venv/bin/activate

# Ativar ambiente (Windows)
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar .env com suas credenciais
# Principais variáveis:
# - GEMINI_API_KEY: Sua API key do Google Gemini
# - SUPABASE_URL: URL do seu projeto Supabase
# - SUPABASE_KEY: Service role key do Supabase
# - API_KEY: Chave de API para autenticação
```

### 3. Executar servidor

```bash
# Modo desenvolvimento
python main.py

# Ou com uvicorn diretamente
uvicorn main:app --reload --port 8001
```

O servidor estará disponível em: http://localhost:8001

## 📡 Endpoints Principais

### Documentação Interativa
- Swagger UI: http://localhost:8001/api/docs
- ReDoc: http://localhost:8001/api/redoc

### Health Check
```bash
curl http://localhost:8001/api/v1/health
```

### Processar E-mail
```bash
curl -X POST http://localhost:8001/api/v1/emails/process \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "email_id": "msg_123",
    "from": "cliente@example.com",
    "to": "support@biofraga.com",
    "subject": "Dúvida sobre produto",
    "body": "Olá, gostaria de saber mais sobre...",
    "received_at": "2025-01-15T10:30:00Z"
  }'
```

## 🧪 Testes

### Testar conexão com Gemini
```bash
curl -X POST http://localhost:8001/api/v1/emails/test-connection \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## 🏗️ Estrutura do Projeto

```
backend-ai/
├── app/
│   ├── api/v1/         # Endpoints da API
│   ├── core/           # Configurações e segurança
│   ├── models/         # Modelos Pydantic
│   ├── services/       # Lógica de negócios
│   └── db/            # Integração com banco
├── main.py            # Entry point
├── requirements.txt   # Dependências
└── .env.example      # Exemplo de configuração
```

## 🔒 Segurança

- Autenticação via Bearer Token (API Key)
- Rate limiting configurado
- CORS habilitado para origens específicas
- Validação de entrada com Pydantic

## 🚀 Deploy

### Docker (em desenvolvimento)
```bash
docker build -t xmx-email-ai .
docker run -p 8001:8000 --env-file .env xmx-email-ai
```

### Produção
- Configure HTTPS
- Use variáveis de ambiente seguras
- Configure logs e monitoramento
- Use um processo manager (gunicorn, supervisor)

## 📝 Notas

- O sistema usa Google Gemini 2.5 Flash por padrão
- Respostas são geradas em português brasileiro
- Cache de 5 minutos para otimização
- Suporte para processamento em lote

## 🤝 Contribuindo

1. Crie uma branch para sua feature
2. Faça commit das mudanças
3. Abra um Pull Request

## 📄 Licença

Privado - Todos os direitos reservados