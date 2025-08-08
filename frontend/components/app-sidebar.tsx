"use client"

import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { User } from '@supabase/supabase-js'
import { createClient } from '@/utils/supabase/client'
import { Home, Inbox, Send, Mail, LogOut, Bot, Sparkles } from "lucide-react"
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarFooter,
} from "@/components/ui/sidebar"
import { Button } from "@/components/ui/button"
import { toast } from 'sonner'
import { Avatar, AvatarFallback } from "@/components/ui/avatar"

const menuItems = [
  {
    title: "Dashboard",
    href: "/dashboard",
    icon: Home,
    description: "Visão geral do sistema"
  },
  {
    title: "Caixa de Entrada",
    href: "/inbox",
    icon: Inbox,
    description: "E-mails recebidos"
  },
  {
    title: "Caixa de Saída",
    href: "/sent",
    icon: Send,
    description: "E-mails enviados"
  },
  {
    title: "Processamento IA",
    href: "/llm",
    icon: Bot,
    description: "Gerenciar respostas automáticas"
  },
]

interface AppSidebarProps {
  user: User
}

export function AppSidebar({ user }: AppSidebarProps) {
  const pathname = usePathname()
  const router = useRouter()

  const handleLogout = async () => {
    try {
      const supabase = createClient()
      await supabase.auth.signOut()
      router.push('/login')
      toast.success('Logout realizado com sucesso')
    } catch (error) {
      toast.error('Erro ao fazer logout')
    }
  }

  const getUserInitials = (email: string) => {
    return email.slice(0, 2).toUpperCase()
  }

  return (
    <Sidebar className="border-r bg-gradient-to-b from-background to-muted/20">
      <SidebarHeader className="border-b px-6 py-5">
        <Link href="/dashboard" className="flex items-center gap-3 group">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg shadow-blue-500/20 transition-all group-hover:shadow-xl group-hover:shadow-blue-500/30 group-hover:scale-105">
            <Mail className="h-6 w-6 text-white" />
          </div>
          <div className="flex flex-col">
            <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-blue-700 bg-clip-text text-transparent">
              XMX MAIL
            </span>
            <span className="text-xs text-muted-foreground">
              Sistema Inteligente
            </span>
          </div>
          <Sparkles className="h-4 w-4 text-yellow-500 ml-auto animate-pulse" />
        </Link>
      </SidebarHeader>
      
      <SidebarContent className="px-3 py-4">
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu className="space-y-1">
              {menuItems.map((item) => {
                const isActive = pathname === item.href
                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton
                      asChild
                      className={`
                        h-12 px-4 
                        transition-all duration-200
                        hover:bg-accent/50
                        ${isActive 
                          ? 'bg-blue-50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400 shadow-sm border-l-4 border-blue-500' 
                          : 'hover:translate-x-1'
                        }
                      `}
                    >
                      <Link href={item.href} className="flex items-center gap-3 w-full">
                        <item.icon className={`h-5 w-5 ${isActive ? 'text-blue-600 dark:text-blue-400' : 'text-muted-foreground'}`} />
                        <div className="flex flex-col flex-1">
                          <span className={`text-sm font-medium ${isActive ? 'text-blue-600 dark:text-blue-400' : ''}`}>
                            {item.title}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {item.description}
                          </span>
                        </div>
                        {isActive && (
                          <div className="h-2 w-2 rounded-full bg-blue-500 animate-pulse ml-auto" />
                        )}
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                )
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      
      <SidebarFooter className="border-t px-4 py-4 mt-auto">
        <div className="flex items-center gap-3">
          <Avatar className="h-10 w-10 border-2 border-muted">
            <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-600 text-white font-semibold">
              {getUserInitials(user.email || '')}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">
              {user.user_metadata?.username || 'Usuário'}
            </p>
            <p className="text-xs text-muted-foreground truncate">
              {user.email}
            </p>
          </div>
          <Button 
            variant="ghost" 
            size="icon"
            onClick={handleLogout}
            className="h-9 w-9 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/30 transition-colors"
            title="Sair do sistema"
          >
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
        
        <div className="mt-4 pt-4 border-t">
          <div className="px-2 py-1.5 text-xs text-muted-foreground text-center">
            © 2025 XMX Email System
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}