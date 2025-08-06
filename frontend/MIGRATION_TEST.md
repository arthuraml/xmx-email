# Instruções de Teste - Migração Node.js para Next.js API Routes

## Visão Geral
Este documento contém instruções para testar a migração completa do backend Node.js para Next.js API Routes. Todos os endpoints foram migrados e agora estão disponíveis diretamente no frontend Next.js.

## Configuração Inicial

### 1. Variáveis de Ambiente
Adicione as seguintes variáveis ao arquivo `.env.local` no frontend:

```bash
# Google OAuth
GOOGLE_CLIENT_ID=seu_client_id
GOOGLE_CLIENT_SECRET=seu_client_secret
GOOGLE_REDIRECT_URI=http://localhost:3000/api/auth/google/callback
GOOGLE_REDIRECT_URI_PROD=https://seu-dominio.com/api/auth/google/callback

# Python Backend
PYTHON_BACKEND_URL=http://localhost:8001
API_KEY=cefc0ee900bc2234c94e0df6566aa4fe1e1703cc42d64b858347cfa83e03b774

# App URL
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### 2. Verificar Supabase
Certifique-se de que a tabela `oauth_tokens` foi criada no Supabase com a seguinte estrutura:

```sql
-- Tabela já criada automaticamente
-- Verifique em: Supabase Dashboard > Table Editor > oauth_tokens
```

## Fluxo de Teste Completo

### 1. Autenticação OAuth com Gmail

#### Teste 1.1: Iniciar Autenticação
```bash
# Via browser ou curl
curl http://localhost:3000/api/auth/google

# Resposta esperada:
{
  "success": true,
  "message": "Visit the URL below to authenticate with Gmail",
  "authUrl": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "instructions": "After authorizing, you will be redirected back to complete the authentication."
}
```

#### Teste 1.2: Callback OAuth
1. Acesse a URL retornada no teste anterior
2. Faça login com sua conta Google
3. Autorize as permissões solicitadas
4. Você será redirecionado para uma página de sucesso
5. Após 5 segundos, será redirecionado para `/llm`

### 2. Testar APIs do Gmail

#### Teste 2.1: Listar Emails da Caixa de Entrada
```bash
# Certifique-se de estar autenticado primeiro
curl http://localhost:3000/api/gmail/inbox?limit=10

# Resposta esperada:
{
  "success": true,
  "messages": [...],
  "count": 10
}
```

#### Teste 2.2: Listar Emails Enviados
```bash
curl http://localhost:3000/api/gmail/sent?limit=10

# Resposta esperada:
{
  "success": true,
  "messages": [...],
  "count": 10
}
```

#### Teste 2.3: Obter Detalhes de um Email
```bash
# Substitua MESSAGE_ID pelo ID de um email real
curl http://localhost:3000/api/gmail/message/MESSAGE_ID

# Resposta esperada:
{
  "success": true,
  "message": {
    "id": "...",
    "from": "...",
    "subject": "...",
    "body": "...",
    ...
  }
}
```

#### Teste 2.4: Marcar Email como Lido
```bash
curl -X POST http://localhost:3000/api/gmail/message/MESSAGE_ID/read

# Resposta esperada:
{
  "success": true
}
```

### 3. Testar Webhooks

#### Teste 3.1: Verificar Conectividade
```bash
curl http://localhost:3000/api/webhook/test

# Resposta esperada:
{
  "success": true,
  "message": "Webhook service is working",
  "python_backend": {
    "url": "http://localhost:8001",
    "status": "connected"
  }
}
```

#### Teste 3.2: Processar Email (Fluxo Completo)

Primeiro, certifique-se de que o backend Python está rodando:
```bash
cd /backend-ai
python -m uvicorn app.main:app --reload --port 8001
```

Então teste o processamento:
```bash
curl -X POST http://localhost:3000/api/webhook/process-email \
  -H "Content-Type: application/json" \
  -d '{
    "email_id": "test123",
    "from": "cliente@example.com",
    "to": "suporte@empresa.com",
    "subject": "Preciso rastrear meu pedido",
    "body": "Olá, gostaria de saber o status do meu pedido. Meu email é cliente@example.com",
    "received_at": "2025-01-06T10:00:00Z"
  }'

# Resposta esperada:
{
  "success": true,
  "email_id": "test123",
  "classification": {
    "is_support": true,
    "is_tracking": true,
    "type": "combined",
    "confidence": 0.95
  },
  "tracking": {
    "found": true,
    "order_id": "ORD-12345",
    "status": "Em trânsito",
    "tracking_code": "BR123456789"
  },
  "response": {
    "subject": "Re: Preciso rastrear meu pedido",
    "body": "...",
    "tone": "professional",
    "requires_followup": false
  }
}
```

#### Teste 3.3: Processar Emails em Lote
```bash
curl -X POST http://localhost:3000/api/webhook/process-batch \
  -H "Content-Type: application/json" \
  -d '{
    "emails": [
      {
        "email_id": "batch1",
        "from": "cliente1@example.com",
        "to": "suporte@empresa.com",
        "subject": "Dúvida sobre produto",
        "body": "Qual o prazo de entrega?"
      },
      {
        "email_id": "batch2",
        "from": "cliente2@example.com",
        "to": "suporte@empresa.com",
        "subject": "Rastreamento",
        "body": "Quero rastrear meu pedido"
      }
    ]
  }'
```

### 4. Testar Rate Limiting

#### Teste 4.1: Gmail API Rate Limit (10 req/min)
```bash
# Execute 11 vezes rapidamente
for i in {1..11}; do
  curl -i http://localhost:3000/api/gmail/inbox?limit=1
  echo ""
done

# Na 11ª requisição, você deve receber:
# Status: 429 Too Many Requests
# Body: {"error": "Too many requests. Please try again later."}
```

#### Teste 4.2: Verificar Headers de Rate Limit
```bash
curl -i http://localhost:3000/api/gmail/inbox?limit=1

# Headers esperados:
# X-RateLimit-Limit: 10
# X-RateLimit-Remaining: 9
# X-RateLimit-Reset: 2025-01-06T10:01:00.000Z
```

### 5. Testar Cache

#### Teste 5.1: Verificar Cache de Emails
```bash
# Primeira requisição (sem cache)
time curl http://localhost:3000/api/gmail/inbox?limit=5

# Segunda requisição imediata (com cache - deve ser mais rápida)
time curl http://localhost:3000/api/gmail/inbox?limit=5
```

## Página LLM no Frontend

### Acessar Interface Visual
1. Navegue para: http://localhost:3000/llm
2. Se não estiver autenticado com Gmail, você verá um botão "Conectar Gmail"
3. Após autenticar, você verá:
   - Lista de emails processados
   - Classificações (Suporte/Rastreamento)
   - Respostas sugeridas
   - Ações disponíveis

### Funcionalidades para Testar
1. **Filtros**: Alternar entre abas (Todos, Suporte, Rastreamento, Pendentes, Enviados)
2. **Visualização**: Clicar em um email para ver detalhes
3. **Edição**: Editar resposta sugerida antes de enviar
4. **Envio**: Enviar resposta para o cliente
5. **Atualização**: Botão de refresh para buscar novos emails

## Troubleshooting

### Problema: "Gmail not connected"
**Solução**: Execute o fluxo de autenticação OAuth primeiro

### Problema: "Rate limit exceeded"
**Solução**: Aguarde o tempo indicado no header `Retry-After`

### Problema: "Python backend disconnected"
**Solução**: 
```bash
cd /backend-ai
python -m uvicorn app.main:app --reload --port 8001
```

### Problema: "User not authenticated"
**Solução**: Faça login no Supabase primeiro em http://localhost:3000/login

## Verificação Final

### Checklist de Migração
- [x] OAuth funciona sem o backend Node.js
- [x] APIs do Gmail conectam diretamente
- [x] Webhooks processam emails corretamente
- [x] Rate limiting está ativo
- [x] Cache está funcionando
- [x] Tokens são salvos no Supabase
- [x] Página LLM integrada com novo sistema

### Próximos Passos para Produção
1. Configurar variáveis de ambiente de produção
2. Atualizar URLs de callback OAuth
3. Configurar webhook do Gmail Push Notifications
4. Ajustar limites de rate limiting conforme necessário
5. Implementar monitoramento e logs
6. Configurar backups automáticos do Supabase

## Comandos Úteis

```bash
# Limpar cache do navegador
# Chrome: Ctrl+Shift+Delete

# Verificar logs do Next.js
npm run dev

# Verificar tabela oauth_tokens no Supabase
# Acesse: https://app.supabase.com > SQL Editor
SELECT * FROM oauth_tokens;

# Testar conexão com Python backend
curl -H "X-API-Key: cefc0ee900bc2234c94e0df6566aa4fe1e1703cc42d64b858347cfa83e03b774" \
  http://localhost:8001/api/v1/health
```

## Conclusão

A migração do backend Node.js para Next.js API Routes está completa. Todos os endpoints foram migrados e testados. O sistema agora:

1. **Simplifica o deployment**: Apenas um aplicativo Next.js no Vercel
2. **Reduz latência**: Não há mais proxy entre frontend e Gmail API
3. **Melhora segurança**: Tokens OAuth salvos no Supabase
4. **Facilita manutenção**: Todo código em TypeScript
5. **Otimiza performance**: Cache integrado e rate limiting

Para deploy em produção, simplesmente faça push para o GitHub e o Vercel fará o deploy automaticamente.