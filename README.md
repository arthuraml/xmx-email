# XMX Email - Gmail Integration

Sistema de gerenciamento de emails integrado com Gmail API para o email support@biofraga.com

## 📋 Pré-requisitos

- Node.js 18+ 
- Conta Google Workspace com email support@biofraga.com
- Credenciais da API do Gmail (Service Account ou OAuth2)

## 🚀 Configuração Rápida

### 1. Configuração do Google Cloud Console

1. Acesse [Google Cloud Console](https://console.cloud.google.com)
2. Crie um novo projeto ou selecione um existente
3. Ative a Gmail API:
   - Menu → APIs e Serviços → Biblioteca
   - Procure por "Gmail API" e ative

### 2. Configuração da Autenticação (Service Account - Recomendado)

1. No Google Cloud Console:
   - Menu → APIs e Serviços → Credenciais
   - Criar credenciais → Conta de serviço
   - Preencha os detalhes e crie
   - Gere uma chave JSON e baixe

2. Configure Domain-Wide Delegation no Google Workspace Admin:
   - Acesse [Admin Console](https://admin.google.com)
   - Segurança → Controle de acesso e dados → Controles da API
   - Gerenciar delegação em todo o domínio
   - Adicione o Client ID da Service Account
   - Adicione os escopos:
     ```
     https://www.googleapis.com/auth/gmail.readonly
     https://www.googleapis.com/auth/gmail.modify
     ```

### 3. Configuração do Projeto

1. Clone o repositório e configure o ambiente:

```bash
# Clone o repositório
git clone [seu-repositorio]
cd xmx-email

# Configure as variáveis de ambiente
cp .env.example .env
```

2. Edite o arquivo `.env` na raiz do projeto:

```env
# Caminho para o arquivo JSON da Service Account
GOOGLE_SERVICE_ACCOUNT_KEY=./credentials/service-account-key.json

# Email do usuário para impersonar
GMAIL_USER_EMAIL=support@biofraga.com

# Configurações do servidor
BACKEND_PORT=3001
NEXT_PUBLIC_API_URL=http://localhost:3001/api
```

3. Coloque o arquivo JSON da Service Account no caminho especificado

### 4. Instalação e Execução

```bash
# Instalar dependências do backend
cd backend
npm install

# Instalar dependências do frontend
cd ../frontend
npm install --legacy-peer-deps

# Executar o backend (em um terminal)
cd ../backend
npm run dev

# Executar o frontend (em outro terminal)
cd ../frontend
npm run dev
```

## 🖥️ Acessando a Aplicação

- Frontend: http://localhost:3000
- Backend API: http://localhost:3001
- Health Check: http://localhost:3001/health

## 📚 Estrutura da API

### Endpoints Disponíveis

- `GET /api/gmail/inbox` - Lista emails da caixa de entrada
- `GET /api/gmail/sent` - Lista emails enviados
- `GET /api/gmail/message/:id` - Detalhes de um email específico
- `POST /api/gmail/message/:id/read` - Marcar email como lido
- `GET /api/gmail/search?q=query` - Buscar emails

## 🔧 Solução de Problemas

### Erro de Autenticação

1. Verifique se o arquivo da Service Account está no caminho correto
2. Confirme que a Domain-Wide Delegation está configurada
3. Verifique se o email no `.env` está correto

### Erro "Next.js cookies() should be awaited"

Este erro já foi corrigido. Se aparecer novamente, verifique se as funções que usam `cookies()` são `async`.

### Dependências com conflitos

Use `npm install --legacy-peer-deps` no frontend devido ao React 19.

## 🛡️ Segurança

- Nunca commite o arquivo `.env` ou credenciais
- Use HTTPS em produção
- Configure CORS apropriadamente
- Implemente rate limiting (já configurado)

## 🔌 Integração com Supabase MCP (Claude Code)

Este projeto inclui configuração para integração com Supabase através do MCP (Model Context Protocol) do Claude Code.

### Configurando o Supabase MCP

1. **Obtenha suas credenciais do Supabase:**
   - Acesse seu projeto no [Supabase Dashboard](https://app.supabase.com)
   - Vá em Settings → General → Reference ID (este é seu `project-ref`)
   - Vá em Account → Access Tokens → Generate New Token

2. **Configure as variáveis de ambiente:**
   
   Adicione ao seu arquivo `.env`:
   ```env
   SUPABASE_PROJECT_REF=seu_project_ref_aqui
   SUPABASE_ACCESS_TOKEN=seu_access_token_aqui
   ```

3. **O arquivo `.mcp.json` já está configurado** no projeto com:
   - Modo read-only para segurança
   - Integração automática com Claude Code
   - Expansão de variáveis de ambiente

4. **Para verificar se o MCP está funcionando:**
   ```bash
   # No Claude Code, execute:
   /mcp
   ```

### Benefícios da Integração

- Acesso direto aos dados do Supabase dentro do Claude Code
- Consultas SQL facilitadas
- Visualização de estrutura de banco de dados
- Modo read-only previne alterações acidentais

## 📦 Deploy

Para deploy em produção:

1. Configure as variáveis de ambiente no seu serviço de hosting
2. Atualize `NEXT_PUBLIC_API_URL` para a URL de produção
3. Configure HTTPS e domínios apropriados
4. Ajuste CORS no backend para aceitar apenas seu domínio

## 🤝 Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request