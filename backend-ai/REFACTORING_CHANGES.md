# Mudanças de Reestruturação do Backend AI

## Data: 11/08/2025

## Resumo
Reestruturação completa dos endpoints do backend-ai para simplificar o fluxo de processamento de e-mails, consolidando classificação e rastreamento em um único endpoint.

## Mudanças Implementadas

### 1. Consolidação de Endpoints

#### Removidos
- `/api/v1/classification/*` - Funcionalidade integrada ao processamento
- `/api/v1/tracking/*` - Funcionalidade integrada ao processamento

#### Mantidos e Melhorados
- `/api/v1/emails/process` - Agora realiza classificação E busca de rastreamento
- `/api/v1/response/generate` - Gera respostas humanizadas

### 2. Novo Fluxo de Processamento

```mermaid
graph LR
    A[Email Recebido] --> B[/emails/process]
    B --> C[Classificação via Gemini]
    C --> D{É Rastreamento?}
    D -->|Sim| E[Busca MySQL]
    D -->|Não| F[Retorna Classificação]
    E --> F
    F --> G[/response/generate]
    G --> H[Resposta Humanizada]
```

### 3. Integração com Banco de Dados MySQL

#### Mudanças no MySQL Service
- **REMOVIDA**: Criação da tabela `tracking_orders`
- **ATUALIZADA**: Consultas agora usam a tabela `orders` existente
- **CHAVES DE BUSCA**:
  - Email do cliente (`email_client`)
  - ID do pedido (`order_id_cartpanda`)
  - Código de rastreamento (`tracking`)

### 4. Novos Modelos de Dados

#### EmailProcessingResponse
```python
{
    "email_id": "msg_123",
    "classification": {
        "is_support": true,
        "is_tracking": true,
        "urgency": "medium",
        "confidence": 0.92,
        "extracted_order_id": "38495799"
    },
    "tracking_data": {
        "found": true,
        "orders": [{
            "order_id": "38495799",
            "tracking_code": "9400150899561052495864",
            "purchase_date": "2025-08-08T11:27:00",
            "status": "shipped"
        }],
        "query_time_ms": 45
    },
    "tokens": {
        "input_tokens": 250,
        "output_tokens": 180,
        "thought_tokens": 50,
        "total_tokens": 480
    },
    "processing_time": 1.234
}
```

## Arquivos Criados

1. **`app/models/processing.py`** - Modelos unificados para processamento
2. **`app/services/processing_service.py`** - Serviço unificado de processamento

## Arquivos Modificados

1. **`app/services/mysql_service.py`**
   - Removida criação de tabela `tracking_orders`
   - Atualizado para usar tabela `orders`
   - Novo método `_parse_tracking_data_from_orders()`

2. **`app/api/v1/emails.py`**
   - Atualizado endpoint `/process` para usar novo serviço
   - Resposta agora usa `EmailProcessingResponse`
   - Adicionado teste de conexões (Gemini + MySQL)

3. **`app/models/response_generation.py`**
   - Removida dependência de modelos antigos
   - `tracking_data` agora aceita Dict ao invés de TrackingData

4. **`app/services/response_service.py`**
   - Atualizado para processar novo formato de tracking_data
   - Suporta múltiplos pedidos na resposta

5. **`main.py`**
   - Removidos routers de classification e tracking
   - Comentários explicativos sobre mudanças

6. **`app/api/v1/__init__.py`**
   - Removidas importações de routers obsoletos

## Benefícios da Reestruturação

### 1. Simplicidade
- Redução de 5 endpoints para 2 principais
- Fluxo linear e intuitivo

### 2. Eficiência
- Uma única chamada ao Gemini para classificação
- Busca automática de rastreamento sem intervenção manual

### 3. Automatização
- Detecção automática de solicitações de rastreamento
- Extração automática de IDs de pedido do texto

### 4. Consistência
- Tokens sempre corretos e padronizados
- Estrutura de resposta unificada

### 5. Manutenibilidade
- Código mais limpo e organizado
- Menos duplicação de lógica

## Exemplo de Uso

### 1. Processar E-mail
```bash
POST /api/v1/emails/process
{
    "email_id": "msg_123",
    "from_address": "cliente@example.com",
    "to_address": "support@company.com",
    "subject": "Onde está meu pedido 38495799?",
    "body": "Gostaria de saber o status do meu pedido...",
    "received_at": "2025-01-11T10:00:00Z"
}
```

### 2. Gerar Resposta
```bash
POST /api/v1/response/generate
{
    "email_id": "msg_123",
    "email_content": {...},
    "classification": {
        "is_support": true,
        "is_tracking": true,
        "extracted_order_id": "38495799"
    },
    "tracking_data": {
        "found": true,
        "orders": [{...}]
    }
}
```

## Configuração Necessária

### Variáveis de Ambiente (.env)
```env
# MySQL Configuration
MYSQL_HOST=24.199.118.99
MYSQL_PORT=3306
MYSQL_DATABASE=homosistemaxmx
MYSQL_USER=xmxaisuport_leitor
MYSQL_PASSWORD=@6H7w5y1XgdBjgWysvKCc

# Gemini Configuration
GEMINI_API_KEY=AIzaSyDu2O4eAFrmoR9apGuv89_vEjDRw_RnKxA
```

## Testes Recomendados

### 1. Teste de Classificação
```bash
curl -X POST http://localhost:8001/api/v1/emails/process \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "email_id": "test_001",
    "from_address": "test@example.com",
    "subject": "Teste de classificação",
    "body": "Este é um teste"
  }'
```

### 2. Teste de Rastreamento
```bash
curl -X POST http://localhost:8001/api/v1/emails/process \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "email_id": "test_002",
    "from_address": "matheuspizarromarques@gmail.com",
    "subject": "Cadê meu pedido?",
    "body": "Quero saber onde está minha encomenda"
  }'
```

### 3. Teste de Conexões
```bash
curl -X POST http://localhost:8001/api/v1/emails/test-connection \
  -H "X-API-Key: your-api-key"
```

## Notas Importantes

1. **Compatibilidade**: Endpoints antigos foram removidos. Atualize integrações.
2. **Performance**: Consultas MySQL agora limitadas a 5 resultados por padrão.
3. **Segurança**: Credenciais MySQL devem ter apenas permissão de leitura.
4. **Monitoramento**: Logs detalhados em `logs/app.log`

## Próximos Passos

1. [ ] Implementar cache de consultas MySQL
2. [ ] Adicionar métricas de performance
3. [ ] Criar dashboard de monitoramento
4. [ ] Implementar testes automatizados
5. [ ] Documentar API com OpenAPI/Swagger