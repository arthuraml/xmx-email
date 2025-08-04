# Plano Detalhado - Sistema de Login Seguro com Supabase

## 📋 Status do Projeto

### ✅ Tarefas Concluídas
1. **Análise da estrutura do projeto**
   - Frontend: Next.js 15, React 19, TypeScript, Tailwind CSS
   - Componentes UI: shadcn/ui
   - Sistema de rotas: App Router

2. **Configuração inicial do Supabase**
   - Instalado `@supabase/supabase-js`
   - Criado arquivo `lib/supabase.ts` com cliente configurado
   - Configuradas variáveis de ambiente no `.env.local`
   - Project URL: `https://gtydmzumlicopgkddabh.supabase.co`

### 🚧 Tarefas Pendentes

## 1. Criar Usuário Admin no Supabase

### Opção A: Via Supabase Dashboard
```sql
-- No SQL Editor do Supabase Dashboard
INSERT INTO auth.users (
  email,
  encrypted_password,
  email_confirmed_at,
  raw_app_meta_data,
  raw_user_meta_data,
  aud,
  role
) VALUES (
  'admin@xmx.com',
  crypt('xmx123', gen_salt('bf')),
  now(),
  '{"provider": "email", "providers": ["email"]}',
  '{"username": "admin", "role": "admin"}',
  'authenticated',
  'authenticated'
);
```

### Opção B: Via Código (Recomendada)
```typescript
// Script para criar usuário admin
import { supabase } from './lib/supabase'

async function createAdminUser() {
  const { data, error } = await supabase.auth.signUp({
    email: 'admin@xmx.com',
    password: 'xmx123',
    options: {
      data: {
        username: 'admin',
        role: 'admin'
      }
    }
  })
  
  if (error) console.error('Erro:', error)
  else console.log('Usuário admin criado:', data)
}
```

## 2. Criar Contexto de Autenticação

### Arquivo: `contexts/AuthContext.tsx`
```typescript
'use client'

import { createContext, useContext, useEffect, useState } from 'react'
import { User } from '@supabase/supabase-js'
import { supabase } from '@/lib/supabase'

interface AuthContextType {
  user: User | null
  loading: boolean
  signIn: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextType>({} as AuthContextType)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Verificar sessão inicial
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null)
      setLoading(false)
    })

    // Escutar mudanças de autenticação
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null)
    })

    return () => subscription.unsubscribe()
  }, [])

  const signIn = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) throw error
  }

  const signOut = async () => {
    const { error } = await supabase.auth.signOut()
    if (error) throw error
  }

  return (
    <AuthContext.Provider value={{ user, loading, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
```

## 3. Atualizar Página de Login

### Arquivo: `app/login/page.tsx`
```typescript
'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Mail, Loader2 } from "lucide-react"
import { toast } from "sonner"

export default function LoginPage() {
  const router = useRouter()
  const { signIn } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      await signIn(email, password)
      toast.success('Login realizado com sucesso!')
      router.push('/dashboard')
    } catch (error: any) {
      toast.error(error.message || 'Erro ao fazer login')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-100 dark:bg-gray-950 p-4">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <div className="flex items-center justify-center mb-4">
            <Mail className="h-8 w-8 text-primary" />
            <h1 className="ml-2 text-3xl font-bold tracking-tighter">XMX MAIL</h1>
          </div>
          <p className="text-gray-500 dark:text-gray-400">Faça login para acessar sua conta.</p>
        </div>
        <div className="rounded-lg border bg-white p-6 shadow-sm dark:bg-gray-900 dark:border-gray-800">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">E-mail</Label>
              <Input 
                id="email" 
                type="email" 
                placeholder="seu@email.com" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required 
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Senha</Label>
              <Input 
                id="password" 
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required 
                disabled={loading}
              />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Entrando...
                </>
              ) : (
                'Entrar'
              )}
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}
```

## 4. Criar Middleware de Autenticação

### Arquivo: `middleware.ts` (raiz do projeto)
```typescript
import { createMiddlewareClient } from '@supabase/auth-helpers-nextjs'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export async function middleware(req: NextRequest) {
  const res = NextResponse.next()
  const supabase = createMiddlewareClient({ req, res })

  const {
    data: { session },
  } = await supabase.auth.getSession()

  // Rotas que requerem autenticação
  const protectedRoutes = ['/dashboard', '/inbox', '/sent']
  const isProtectedRoute = protectedRoutes.some(route => 
    req.nextUrl.pathname.startsWith(route)
  )

  // Se é rota protegida e não há sessão, redirecionar para login
  if (isProtectedRoute && !session) {
    return NextResponse.redirect(new URL('/login', req.url))
  }

  // Se está logado e tenta acessar login, redirecionar para dashboard
  if (req.nextUrl.pathname === '/login' && session) {
    return NextResponse.redirect(new URL('/dashboard', req.url))
  }

  return res
}

export const config = {
  matcher: ['/dashboard/:path*', '/inbox/:path*', '/sent/:path*', '/login']
}
```

## 5. Atualizar Layout do App

### Arquivo: `app/(app)/layout.tsx`
```typescript
import { redirect } from 'next/navigation'
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/app-sidebar"

export default async function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const supabase = createServerComponentClient({ cookies })
  
  const {
    data: { session },
  } = await supabase.auth.getSession()

  if (!session) {
    redirect('/login')
  }

  return (
    <SidebarProvider>
      <AppSidebar user={session.user} />
      <main className="flex-1">
        <SidebarTrigger />
        {children}
      </main>
    </SidebarProvider>
  )
}
```

## 6. Implementar Logout no Sidebar

### Arquivo: `components/app-sidebar.tsx`
```typescript
'use client'

import { useRouter } from 'next/navigation'
import { User } from '@supabase/supabase-js'
import { supabase } from '@/lib/supabase'
import { Button } from '@/components/ui/button'
import { LogOut } from 'lucide-react'
import { toast } from 'sonner'

interface AppSidebarProps {
  user: User
}

export function AppSidebar({ user }: AppSidebarProps) {
  const router = useRouter()

  const handleLogout = async () => {
    try {
      await supabase.auth.signOut()
      router.push('/login')
      toast.success('Logout realizado com sucesso')
    } catch (error) {
      toast.error('Erro ao fazer logout')
    }
  }

  return (
    <aside>
      {/* ... conteúdo existente do sidebar ... */}
      
      <div className="mt-auto p-4 border-t">
        <div className="flex items-center justify-between">
          <div className="text-sm">
            <p className="font-medium">{user.email}</p>
            <p className="text-gray-500">
              {user.user_metadata?.username || 'Usuário'}
            </p>
          </div>
          <Button 
            variant="ghost" 
            size="icon"
            onClick={handleLogout}
            title="Sair"
          >
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </aside>
  )
}
```

## 7. Atualizar Layout Principal

### Arquivo: `app/layout.tsx`
```typescript
import { AuthProvider } from '@/contexts/AuthContext'
import { Toaster } from 'sonner'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR">
      <body>
        <AuthProvider>
          {children}
          <Toaster />
        </AuthProvider>
      </body>
    </html>
  )
}
```

## 8. Configurar Políticas RLS no Supabase

### No Supabase Dashboard:
1. Navegar para Authentication > Policies
2. Habilitar RLS em todas as tabelas necessárias
3. Criar políticas básicas:

```sql
-- Exemplo de política para tabela de emails
CREATE POLICY "Usuários podem ver apenas seus próprios emails" 
ON public.emails FOR SELECT 
USING (auth.uid() = user_id);

-- Política para admin ver todos os emails
CREATE POLICY "Admin pode ver todos os emails" 
ON public.emails FOR ALL 
USING (
  auth.jwt() ->> 'user_metadata'::text)::jsonb ->> 'role' = 'admin'
);
```

## 📦 Dependências Adicionais Necessárias

```bash
npm install @supabase/auth-helpers-nextjs sonner --legacy-peer-deps
```

## 🔒 Segurança e Boas Práticas

1. **Variáveis de Ambiente**
   - Nunca commitar `.env.local`
   - Adicionar ao `.gitignore`

2. **Validação de Dados**
   - Validar inputs no frontend e backend
   - Sanitizar dados antes de enviar ao banco

3. **Rate Limiting**
   - Implementar limite de tentativas de login
   - Bloquear IPs após múltiplas falhas

4. **HTTPS**
   - Sempre usar conexão segura em produção
   - Configurar headers de segurança

## 🚀 Próximos Passos (Após MVP)

1. **Funcionalidades de Usuário**
   - Cadastro de novos usuários
   - Recuperação de senha
   - Perfil do usuário
   - Upload de avatar

2. **Segurança Avançada**
   - Autenticação 2FA
   - Login com OAuth (Google, GitHub)
   - Logs de auditoria
   - Detecção de login suspeito

3. **Melhorias de UX**
   - Remember me
   - Login social
   - Onboarding para novos usuários
   - Tema claro/escuro persistente

4. **Performance**
   - Cache de sessão
   - Prefetch de dados do usuário
   - Lazy loading de componentes

## 📝 Notas de Implementação

- O Supabase Auth já cuida do hash de senhas automaticamente
- Sessions são gerenciadas via cookies httpOnly
- Tokens JWT são renovados automaticamente
- O middleware garante proteção server-side das rotas

## 🐛 Troubleshooting Comum

1. **Erro de CORS**: Verificar configuração do Supabase URL
2. **Session não persiste**: Verificar cookies e middleware
3. **Redirect loops**: Verificar lógica do middleware
4. **401 Unauthorized**: Verificar RLS policies

---

**Última atualização**: Janeiro 2025
**Projeto**: XMX Email - Sistema de Login Seguro