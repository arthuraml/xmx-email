# 📧 Instruções para Testar o Sistema de Processamento de E-mails com LLM

## 🚀 Visão Geral do Sistema

O sistema processa e-mails em tempo real através de 3 etapas:
1. **Classificação**: Determina se é suporte e/ou rastreamento
2. **Busca de Rastreamento**: Consulta MySQL se necessário
3. **Geração de Resposta**: Cria resposta contextualizada com LLM

## 📋 Pré-requisitos

### 1. Configurar Variáveis de Ambiente
Edite o arquivo `.env` na raiz do projeto e configure:

```env
# MySQL Database Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=xmx_tracking
MYSQL_USER=root
MYSQL_PASSWORD=sua_senha_mysql  # ⚠️ CONFIGURE SUA SENHA
```

### 2. Criar Banco de Dados MySQL

```sql
-- Criar database
CREATE DATABASE IF NOT EXISTS xmx_tracking;
USE xmx_tracking;

-- Criar tabela de rastreamento
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 3. Inserir Dados de Teste no MySQL

```sql
-- Inserir alguns pedidos de teste
INSERT INTO tracking_orders (
    customer_email, 
    order_id, 
    tracking_code, 
    carrier, 
    status, 
    last_location, 
    last_update,
    estimated_delivery,
    recipient_name,
    delivery_address,
    tracking_json
) VALUES 
(
    'cliente1@example.com',
    'PED-2025-001',
    'BR123456789BR',
    'Correios',
    'EM_TRANSITO',
    'São Paulo/SP',
    '2025-01-06 14:30:00',
    '2025-01-09 18:00:00',
    'João Silva',
    'Rua das Flores, 123 - São Paulo/SP',
    '[{"date":"2025-01-04T10:00:00","status":"Postado","location":"São Paulo/SP"},{"date":"2025-01-05T14:00:00","status":"Em trânsito","location":"Curitiba/PR"}]'
),
(
    'cliente2@example.com',
    'PED-2025-002',
    'ML987654321BR',
    'Mercado Envios',
    'ENTREGUE',
    'Rio de Janeiro/RJ',
    '2025-01-05 16:45:00',
    '2025-01-05 16:45:00',
    'Maria Santos',
    'Av. Principal, 456 - Rio de Janeiro/RJ',
    '[{"date":"2025-01-03T09:00:00","status":"Coletado","location":"São Paulo/SP"},{"date":"2025-01-05T16:45:00","status":"Entregue","location":"Rio de Janeiro/RJ"}]'
),
(
    'teste@example.com',
    'PED-2025-TEST',
    'LG555555555BR',
    'Loggi',
    'SAIU_PARA_ENTREGA',
    'Belo Horizonte/MG',
    '2025-01-06 08:00:00',
    '2025-01-06 18:00:00',
    'Cliente Teste',
    'Praça Central, 789 - Belo Horizonte/MG',
    '[{"date":"2025-01-05T10:00:00","status":"Em trânsito","location":"São Paulo/SP"},{"date":"2025-01-06T08:00:00","status":"Saiu para entrega","location":"Belo Horizonte/MG"}]'
);
```

## 🔧 Iniciar os Serviços

### 1. Backend Python (Terminal 1)
```bash
cd backend-ai

# Instalar dependências (primeira vez)
pip install -r requirements.txt

# Iniciar servidor
python main.py
```
O servidor Python rodará em `http://localhost:8001`

### 2. Backend Node.js (Terminal 2)
```bash
cd backend

# Instalar dependências (primeira vez)
npm install

# Iniciar servidor
npm run dev
```
O servidor Node.js rodará em `http://localhost:3001`

### 3. Frontend Next.js (Terminal 3)
```bash
cd frontend

# Instalar dependências (primeira vez)
npm install --legacy-peer-deps

# Iniciar servidor
npm run dev
```
O frontend rodará em `http://localhost:3000`

## 🧪 Testar o Sistema

### Teste 1: Classificação de E-mail
```bash
# Testar endpoint de classificação
curl -X POST http://localhost:8001/api/v1/classification/classify \
  -H "Content-Type: application/json" \
  -H "X-API-Key: cefc0ee900bc2234c94e0df6566aa4fe1e1703cc42d64b858347cfa83e03b774" \
  -d '{
    "email_id": "test_001",
    "from_address": "cliente1@example.com",
    "to_address": "support@biofraga.com",
    "subject": "Onde está meu pedido?",
    "body": "Olá, gostaria de saber o status da minha entrega. Comprei há 3 dias.",
    "received_at": "2025-01-06T10:00:00Z"
  }'
```

### Teste 2: Busca de Rastreamento
```bash
# Testar busca de rastreamento
curl -X POST http://localhost:8001/api/v1/tracking/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: cefc0ee900bc2234c94e0df6566aa4fe1e1703cc42d64b858347cfa83e03b774" \
  -d '{
    "email_id": "test_001",
    "sender_email": "cliente1@example.com"
  }'
```

### Teste 3: Geração de Resposta
```bash
# Testar geração de resposta
curl -X POST http://localhost:8001/api/v1/response/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: cefc0ee900bc2234c94e0df6566aa4fe1e1703cc42d64b858347cfa83e03b774" \
  -d '{
    "email_id": "test_001",
    "email_content": {
      "from": "cliente1@example.com",
      "to": "support@biofraga.com",
      "subject": "Onde está meu pedido?",
      "body": "Olá, gostaria de saber o status da minha entrega."
    },
    "classification": {
      "is_support": false,
      "is_tracking": true,
      "urgency": "medium"
    },
    "tracking_data": {
      "order_id": "PED-2025-001",
      "tracking_code": "BR123456789BR",
      "carrier": "Correios",
      "status": "EM_TRANSITO",
      "last_location": "São Paulo/SP"
    }
  }'
```

### Teste 4: Fluxo Completo via Webhook
```bash
# Testar o fluxo completo através do webhook
curl -X POST http://localhost:3001/api/webhook/process-email \
  -H "Content-Type: application/json" \
  -d '{
    "email_id": "test_002",
    "from": "cliente1@example.com",
    "to": "support@biofraga.com",
    "subject": "Produto com defeito e onde está minha devolução?",
    "body": "Recebi o produto com defeito e já solicitei devolução. Quero saber onde está o envio da devolução.",
    "received_at": "2025-01-06T12:00:00Z"
  }'
```

## 🖥️ Testar Interface Web

1. Acesse `http://localhost:3000`
2. Faça login (se necessário)
3. Navegue até a página **LLM** no menu lateral
4. Você verá:
   - Lista de e-mails processados
   - Classificações (suporte/rastreamento)
   - Respostas sugeridas pela LLM
   - Dados de rastreamento quando disponíveis
   - Ações: Aprovar, Editar, Enviar resposta

## 📊 Verificar Dados no Supabase

Acesse as tabelas no Supabase Dashboard:
- `processed_emails` - E-mails classificados
- `llm_responses` - Respostas geradas
- `tracking_requests` - Consultas de rastreamento
- `email_analytics` - Métricas agregadas

## 🔍 Cenários de Teste

### Cenário 1: E-mail de Rastreamento
- E-mail pedindo "onde está meu pedido"
- Sistema deve classificar como `is_tracking = true`
- Buscar dados no MySQL
- Gerar resposta com informações de rastreamento

### Cenário 2: E-mail de Suporte
- E-mail com "produto com defeito"
- Sistema deve classificar como `is_support = true`
- Gerar resposta de suporte sem rastreamento

### Cenário 3: E-mail Combinado
- E-mail com defeito E pedindo rastreamento
- Sistema deve classificar ambos como `true`
- Buscar rastreamento E gerar resposta combinada

### Cenário 4: E-mail sem Rastreamento no BD
- Use e-mail de `naoexiste@example.com`
- Sistema deve lidar graciosamente
- Sugerir que cliente forneça mais informações

## 🐛 Troubleshooting

### Erro de Conexão MySQL
```bash
# Verificar se MySQL está rodando
sudo systemctl status mysql

# Testar conexão
mysql -u root -p -e "SELECT 1"
```

### Erro de API Key
Verifique se a API key está correta no `.env`:
```
API_KEY=cefc0ee900bc2234c94e0df6566aa4fe1e1703cc42d64b858347cfa83e03b774
```

### Erro do Gemini
Verifique se a GEMINI_API_KEY está configurada e válida no `.env`

### Logs de Debug
- Python: `backend-ai/logs/app.log`
- Node.js: Console do terminal
- Frontend: Console do navegador (F12)

## ✅ Checklist de Validação

- [ ] Backend Python inicia sem erros
- [ ] Backend Node.js conecta com Python
- [ ] Frontend carrega página LLM
- [ ] Classificação identifica corretamente suporte/rastreamento
- [ ] Busca no MySQL retorna dados quando existe
- [ ] LLM gera respostas apropriadas
- [ ] Interface mostra e-mails processados
- [ ] Botões de aprovar/enviar funcionam
- [ ] Dados são salvos no Supabase

## 📝 Notas Importantes

1. **Senha MySQL**: Configure sua senha real no `.env`
2. **Limites de Rate**: O sistema tem rate limiting configurado
3. **Tokens LLM**: Monitore uso de tokens no console
4. **Cache**: Respostas podem ser cacheadas por 5 minutos
5. **Segurança**: Em produção, use HTTPS e autenticação robusta