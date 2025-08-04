# 🚀 Quick Start - Backend AI

## ✅ Status Atual

O backend está **completamente configurado** e pronto para executar após adicionar as chaves de API.

## 📋 Próximos Passos

### 1. Configure as Chaves de API

Edite o arquivo `.env` na **raiz do projeto** (não no backend-ai):

```bash
cd /media/arthuraml/SSD2/projetos/xmx-email
nano .env  # ou use seu editor preferido
```

Preencha as seguintes chaves:

```env
# Gere chaves seguras com: python -c "import secrets; print(secrets.token_hex(32))"
API_KEY=sua-chave-segura-aqui
SECRET_KEY=sua-chave-secreta-aqui

# Obtenha em https://aistudio.google.com/apikey
GEMINI_API_KEY=AIzaSy...

# Do painel Supabase > Settings > API > service_role key
SUPABASE_KEY=eyJhbGc...
```

### 2. Teste a Configuração

```bash
cd backend-ai
python test_setup.py
```

### 3. Execute o Backend

```bash
# Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Executar servidor
python main.py
```

O servidor estará disponível em:
- API: http://localhost:8001
- Docs: http://localhost:8001/api/docs
- ReDoc: http://localhost:8001/api/redoc

## 🧪 Testando a API

### Health Check
```bash
curl http://localhost:8001/api/v1/health
```

### Processar Email (exemplo)
```bash
curl -X POST http://localhost:8001/api/v1/emails/process \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sua-api-key-aqui" \
  -d '{
    "from": "cliente@example.com",
    "to": "support@biofraga.com",
    "subject": "Preciso de ajuda com meu pedido",
    "body": "Olá, meu pedido #12345 ainda não chegou. Podem verificar?",
    "received_at": "2025-01-04T12:00:00Z"
  }'
```

## 📁 Estrutura do Backend

```
backend-ai/
├── main.py              # Aplicação principal
├── requirements.txt     # Dependências Python
├── test_setup.py       # Script de teste de configuração
├── app/
│   ├── api/v1/         # Endpoints da API
│   ├── core/           # Configurações e clientes
│   ├── models/         # Modelos Pydantic
│   ├── db/             # Integração Supabase
│   └── services/       # Lógica de negócio
└── logs/               # Logs da aplicação
```

## 🔧 Comandos Úteis

```bash
# Instalar/atualizar dependências
pip install -r requirements.txt

# Executar testes
pytest

# Formatar código
black .

# Verificar código
flake8 .

# Type checking
mypy .
```

## 📚 Documentação

- [PLANO_BACKEND_AI_GEMINI.md](../PLANO_BACKEND_AI_GEMINI.md) - Plano detalhado de implementação
- [INSTRUCOES_CHAVES_API.md](../INSTRUCOES_CHAVES_API.md) - Como obter as chaves de API
- [README.md](README.md) - Documentação completa do backend

## ⚠️ Troubleshooting

### Erro de importação
```bash
# Reinstalar dependências
pip uninstall -y -r requirements.txt
pip install -r requirements.txt
```

### Erro de variáveis de ambiente
- Verifique se o arquivo `.env` está na raiz do projeto (não no backend-ai)
- Confirme que as chaves não têm espaços ou aspas extras

### Porta já em uso
```bash
# Matar processo na porta 8001
lsof -ti:8001 | xargs kill -9  # Linux/Mac
# ou mude a porta no .env: API_PORT=8002
```