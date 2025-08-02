# CLAUDE.md - XMX Email Frontend

## Visão Geral do Projeto
Este é o frontend de um sistema de gerenciamento de emails construído com Next.js 15, React 19, TypeScript e Tailwind CSS.

## Estrutura do Projeto
```
frontend/
├── app/                    # App Router do Next.js
│   ├── (app)/             # Grupo de rotas autenticadas
│   │   ├── layout.tsx     # Layout com sidebar (async)
│   │   ├── dashboard/     # Página principal
│   │   ├── inbox/         # Caixa de entrada (integrado Gmail)
│   │   └── sent/          # Emails enviados (integrado Gmail)
│   ├── api/gmail/         # API Routes para Gmail
│   │   ├── inbox/         # GET emails da caixa de entrada
│   │   ├── sent/          # GET emails enviados
│   │   └── message/[id]/  # GET/POST detalhes e ações
│   ├── login/             # Página de login
│   └── globals.css        # Estilos globais
├── components/            # Componentes React
│   ├── ui/               # Componentes UI (shadcn/ui)
│   ├── app-sidebar.tsx   # Sidebar da aplicação
│   ├── email-list.tsx    # Lista de emails com loading/empty states
│   └── email-preview.tsx # Preview detalhado de email
├── lib/                  # Utilitários
│   ├── utils.ts         # Funções auxiliares
│   └── gmail.ts         # API client e helpers do Gmail
└── package.json         # Dependências do projeto
```

## Tecnologias Principais
- **Next.js 15.2.4** - Framework React com App Router
- **React 19** - Biblioteca UI
- **TypeScript** - Tipagem estática
- **Tailwind CSS** - Estilização
- **shadcn/ui** - Componentes UI
- **Lucide React** - Ícones

## Comandos Importantes
```bash
# Instalar dependências (com flag para resolver conflitos de peer deps)
npm install --legacy-peer-deps

# Iniciar servidor de desenvolvimento
npm run dev

# Build para produção
npm run build

# Executar build de produção
npm start

# Verificar tipos TypeScript
npm run type-check

# Executar linter
npm run lint
```

## Notas de Desenvolvimento

### Erro de Cookies Assíncronos
O Next.js 15 requer que `cookies()` seja awaited. Em `app/(app)/layout.tsx`, a função deve ser `async`:
```typescript
export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const cookieStore = await cookies()
  // ...
}
```

### Conflitos de Dependências
O projeto usa React 19, mas algumas dependências (como `vaul`) esperam React 18. Use `--legacy-peer-deps` ao instalar.

### Estrutura de Rotas
- `/` - Redireciona para `/dashboard`
- `/login` - Tela de autenticação
- `/dashboard` - Página principal (requer autenticação)
- `/inbox` - Caixa de entrada de emails
- `/sent` - Emails enviados

### Componentes Principais
- **AppSidebar**: Navegação lateral com links para Dashboard, Inbox e Sent
- **EmailList**: Lista de emails com skeleton loading, empty states e seleção
- **EmailPreview**: Visualização detalhada com ações (marcar como lido)
- **UI Components**: Baseados em shadcn/ui (Button, Card, Sidebar, etc.)

## Integração Gmail API

### Backend API (Node.js/Express)
O backend em `/backend` fornece:
- Autenticação via Service Account com Domain-Wide Delegation
- Cache de mensagens para melhor performance
- Rate limiting para proteção
- Endpoints RESTful para inbox, sent, detalhes e ações

### Frontend Integration
- **API Routes**: Proxy requests para o backend
- **Gmail Client**: Biblioteca helper em `lib/gmail.ts`
- **Real-time Updates**: Botão de refresh manual
- **Error Handling**: Estados de erro com retry

### Fluxo de Dados
1. Frontend faz request para API Route Next.js
2. API Route proxy para backend Express
3. Backend autentica com Gmail API via Service Account
4. Dados são cacheados e retornados
5. Frontend exibe com loading/error states

## Próximos Passos
1. ~~Implementar autenticação real~~ ✓ (Service Account)
2. ~~Conectar com API backend~~ ✓
3. Adicionar funcionalidade de composição de emails
4. Implementar busca e filtros avançados
5. Adicionar notificações em tempo real (webhooks)
6. Implementar paginação para grandes volumes
7. Adicionar suporte para anexos