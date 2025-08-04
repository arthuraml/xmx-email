# Instruções para Obter as Chaves de API

## 1. Google Gemini API Key

1. Acesse: https://aistudio.google.com/apikey
2. Faça login com sua conta Google
3. Clique em "Create API Key"
4. Copie a chave gerada
5. Cole no arquivo `.env` em `GEMINI_API_KEY=`

## 2. Supabase Service Role Key

1. Acesse seu projeto no Supabase: https://app.supabase.com
2. Vá em Settings (ícone de engrenagem)
3. Clique em "API" no menu lateral
4. Em "Project API keys", copie a **service_role** key (NÃO use a anon key!)
5. Cole no arquivo `.env` em `SUPABASE_KEY=`

⚠️ **IMPORTANTE**: A service role key tem acesso total ao banco de dados. Nunca a exponha publicamente!

## 3. API_KEY e SECRET_KEY

Estas são chaves que você deve criar para proteger seu backend:

### API_KEY
Gere uma chave aleatória forte:
```bash
# Linux/Mac
openssl rand -hex 32

# Ou use Python
python -c "import secrets; print(secrets.token_hex(32))"
```

### SECRET_KEY
Gere outra chave aleatória para JWT:
```bash
# Linux/Mac
openssl rand -hex 32

# Ou use Python
python -c "import secrets; print(secrets.token_hex(32))"
```

## 4. Exemplo Final no .env

```env
# Backend AI Configuration
API_KEY=a1b2c3d4e5f6789...  # Sua chave gerada
SECRET_KEY=z9y8x7w6v5u4...  # Sua chave gerada
GEMINI_API_KEY=AIzaSy...     # Chave do Google Gemini
SUPABASE_URL=https://gtydmzumlicopgkddabh.supabase.co
SUPABASE_KEY=eyJhbGc...      # Service role key do Supabase
```

## 5. Testando

Após configurar, teste o backend:

```bash
cd backend-ai
source venv/bin/activate  # Ativar ambiente virtual
python main.py
```

Acesse http://localhost:8001/api/docs para ver a documentação da API.