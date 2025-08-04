# XMX Email - Sistema de Gerenciamento de E-mails com Gmail e Supabase

<div align="center">
  <img src="https://img.shields.io/badge/Next.js-15.2.4-000000?style=for-the-badge&logo=next.js&logoColor=white" />
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/TypeScript-5-3178C6?style=for-the-badge&logo=typescript&logoColor=white" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" />
  <img src="https://img.shields.io/badge/Supabase-Latest-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white" />
</div>

## 📋 Visão Geral

XMX Email é um sistema moderno de gerenciamento de e-mails que integra Gmail API com autenticação Supabase. Desenvolvido com Next.js 15, React 19 e TypeScript, oferece uma interface intuitiva para gerenciar e-mails corporativos.

### 🌟 Principais Funcionalidades

- ✉️ **Integração Gmail API** - Acesso completo à caixa de entrada e e-mails enviados
- 🔐 **Autenticação Segura** - Sistema de login com Supabase Auth
- 🎨 **Interface Moderna** - UI responsiva com shadcn/ui e Tailwind CSS
- 🚀 **Performance Otimizada** - Cache inteligente e loading states
- 🔌 **Integração MCP** - Suporte para Claude Code com Supabase MCP
- 📱 **100% Responsivo** - Funciona perfeitamente em desktop e mobile

## 🏗️ Arquitetura do Projeto

```
xmx-email/
├── frontend/                 # Aplicação Next.js
│   ├── app/                 # App Router (Next.js 15)
│   │   ├── (app)/          # Rotas autenticadas
│   │   │   ├── dashboard/  # Painel principal
│   │   │   ├── inbox/      # Caixa de entrada
│   │   │   └── sent/       # E-mails enviados
│   │   ├── api/            # API Routes
│   │   └── login/          # Página de autenticação
│   ├── components/         # Componentes React
│   │   ├── ui/            # shadcn/ui components
│   │   └── ...            # Componentes customizados
│   ├── contexts/          # Context API (AuthContext)
│   ├── lib/               # Utilitários e configurações
│   └── utils/             # Helpers do Supabase
│
├── backend/                # API Node.js/Express
│   ├── src/
│   │   ├── config/        # Configurações (Google Auth)
│   │   ├── routes/        # Endpoints da API
│   │   └── services/      # Lógica de negócios (Gmail)
│   └── server.js          # Servidor Express
│
└── docs/                   # Documentação adicional
    ├── CLAUDE.md          # Guia para Claude Code
    └── PLANO_LOGIN_SUPABASE.md
```

## 🚀 Início Rápido

### Pré-requisitos

- Node.js 18+
- Conta Google Workspace
- Projeto Supabase configurado
- Credenciais da Gmail API

### 1. Clone o Repositório

```bash
git clone [seu-repositorio]
cd xmx-email
```

### 2. Configure as Variáveis de Ambiente

#### Frontend (.env.local)
```env
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://gtydmzumlicopgkddabh.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=seu_anon_key_aqui

# API Backend
NEXT_PUBLIC_API_URL=http://localhost:3001/api
```

#### Backend (.env)
```env
# Google Service Account
GOOGLE_SERVICE_ACCOUNT_KEY=./credentials/service-account-key.json
GMAIL_USER_EMAIL=support@biofraga.com

# Server
BACKEND_PORT=3001
```

### 3. Instale as Dependências

```bash
# Frontend
cd frontend
npm install --legacy-peer-deps

# Backend
cd ../backend
npm install
```

### 4. Execute o Projeto

```bash
# Terminal 1 - Backend
cd backend
npm run dev

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Acesse: http://localhost:3000

## 📚 Stack Tecnológica

### Frontend
- **Framework**: Next.js 15.2.4 (App Router)
- **UI Library**: React 19
- **Linguagem**: TypeScript 5
- **Estilização**: Tailwind CSS 3.4
- **Componentes**: shadcn/ui
- **Autenticação**: Supabase Auth (@supabase/ssr)
- **Ícones**: Lucide React
- **Notificações**: Sonner

### Backend
- **Runtime**: Node.js
- **Framework**: Express 4.19
- **API Integration**: Google APIs (Gmail)
- **Cache**: node-cache
- **Segurança**: CORS, Rate Limiting
- **Autenticação**: Google Service Account

## 🔐 Autenticação e Segurança

### Sistema de Login

1. **Supabase Auth** - Gerenciamento completo de sessões
2. **Middleware Protection** - Rotas protegidas server-side
3. **Context API** - Estado global de autenticação
4. **Cookies HttpOnly** - Sessões seguras

### Configuração Gmail API

1. **Service Account** com Domain-Wide Delegation
2. **OAuth Scopes** configurados:
   - `gmail.readonly`
   - `gmail.modify`
3. **Rate Limiting** implementado
4. **Cache de 5 minutos** para otimização

## 🔌 Integração Supabase MCP

### Configuração para Claude Code

1. **Arquivo .mcp.json** já configurado
2. **Variáveis necessárias**:
   ```env
   SUPABASE_PROJECT_REF=gtydmzumlicopgkddabh
   SUPABASE_ACCESS_TOKEN=seu_token_aqui
   ```
3. **Verificar integração**:
   ```bash
   # No Claude Code
   /mcp
   ```

## 📱 Funcionalidades Implementadas

### ✅ Completas
- Sistema de login/logout com Supabase
- Listagem de e-mails (inbox/sent)
- Visualização detalhada de e-mails
- Marcar como lido
- Interface responsiva com sidebar
- Loading states e empty states
- Cache inteligente

### 🚧 Em Desenvolvimento
- Composição de e-mails
- Busca e filtros avançados
- Anexos de arquivos
- Notificações em tempo real
- Paginação para grandes volumes

## 🛠️ Comandos Úteis

### Frontend
```bash
npm run dev      # Desenvolvimento
npm run build    # Build de produção
npm run start    # Executar build
npm run lint     # Verificar código
```

### Backend
```bash
npm run dev      # Desenvolvimento (nodemon)
npm start        # Produção
```

## 📋 Configuração Completa

### 1. Google Cloud Console

1. Criar projeto ou usar existente
2. Ativar Gmail API
3. Criar Service Account
4. Configurar Domain-Wide Delegation
5. Baixar chave JSON

### 2. Supabase Dashboard

1. Criar novo projeto
2. Configurar autenticação
3. Obter URL e Anon Key
4. Criar usuário admin (opcional)

### 3. Deploy em Produção

1. Configure variáveis no serviço de hosting
2. Use HTTPS obrigatoriamente
3. Configure CORS apropriadamente
4. Implemente monitoramento

## 🐛 Solução de Problemas

### Erros Comuns

1. **"cookies() should be awaited"**
   - Solução: Funções que usam cookies devem ser async

2. **Conflitos de dependências React 19**
   - Solução: Use `npm install --legacy-peer-deps`

3. **Erro de autenticação Gmail**
   - Verificar Service Account e Domain-Wide Delegation

4. **Session não persiste**
   - Verificar configuração do middleware Supabase

## 🤝 Contribuindo

1. Fork o projeto
2. Crie sua feature branch (`git checkout -b feature/NovaFuncionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/NovaFuncionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob licença privada. Todos os direitos reservados.

## 👥 Equipe

- **Desenvolvimento**: Equipe XMX
- **Email de Suporte**: support@biofraga.com

## 📞 Suporte

Para questões e suporte:
- 📧 Email: support@biofraga.com
- 📚 Documentação: Ver pasta `/docs`
- 🐛 Issues: GitHub Issues

---

<div align="center">
  <strong>XMX Email</strong> - Sistema profissional de gerenciamento de e-mails
  <br>
  Desenvolvido com ❤️ pela equipe XMX
</div>