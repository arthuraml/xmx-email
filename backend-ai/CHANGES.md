# Mudanças Realizadas no Backend AI

## 📝 Resumo das Modificações

### 1. ❌ Remoção de Funcionalidades
- **Removidos endpoints de Prompts**: `/api/v1/prompts/*`
- **Removidos endpoints de Analytics**: `/api/v1/analytics/*`
- **Removidos arquivos**:
  - `app/api/v1/prompts.py`
  - `app/api/v1/analytics.py`
  - `app/models/prompt.py`

### 2. 📄 System Prompt em Arquivo
- **Criado arquivo**: `system_prompt.txt` na raiz do backend-ai
- **Funcionalidade**: O prompt do sistema agora é lido deste arquivo
- **Benefício**: Permite editar o prompt sem modificar código
- **Função nova**: `get_system_prompt()` em `app/core/gemini.py`

### 3. 📊 Captura de Tokens
- **Novos campos** adicionados ao `EmailProcessingResult`:
  - `prompt_tokens`: Tokens de entrada (prompt)
  - `output_tokens`: Tokens de saída (resposta)
  - `thought_tokens`: Tokens de pensamento (modelos 2.5)
  - `total_tokens`: Total de tokens utilizados
  
- **Implementação**: 
  - Captura de `usage_metadata` da resposta do Gemini
  - Logging detalhado do uso de tokens
  - Retorno das informações em todas as respostas da API

### 4. 🔧 Arquivos Modificados
- `main.py`: Removidos imports e routers de prompts/analytics
- `app/api/v1/__init__.py`: Removidos exports desnecessários
- `app/models/__init__.py`: Removidos imports de modelos de prompt
- `app/core/config.py`: Substituído `DEFAULT_SYSTEM_PROMPT` por `SYSTEM_PROMPT_FILE`
- `app/core/gemini.py`: 
  - Adicionada função `get_system_prompt()`
  - Modificada `analyze_email_with_gemini()` para capturar tokens
- `app/services/gemini_service.py`: Modificado para usar prompt do arquivo
- `app/models/response.py`: Adicionados campos de tokens

## 💡 Como Usar

### Editar System Prompt
```bash
# Edite o arquivo diretamente
nano system_prompt.txt
# Ou
vim system_prompt.txt
```

### Visualizar Uso de Tokens
As respostas da API agora incluem:
```json
{
  "status": "completed",
  "email_id": "msg_123",
  "decision": "respond",
  "confidence": 0.95,
  "prompt_tokens": 250,
  "output_tokens": 180,
  "thought_tokens": 0,
  "total_tokens": 430,
  ...
}
```

## 🚀 Benefícios
1. **Simplicidade**: API mais focada apenas no processamento de emails
2. **Flexibilidade**: System prompt editável sem redeployment
3. **Transparência**: Visibilidade completa do uso de tokens
4. **Economia**: Monitoramento de custos através dos tokens