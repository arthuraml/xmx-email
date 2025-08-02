"use client"

import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { User } from '@supabase/supabase-js'
import { createClient } from '@/utils/supabase/client'
import { Home, Inbox, Send, Mail, LogOut } from "lucide-react"
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

const menuItems = [
  {
    title: "Dashboard",
    href: "/dashboard",
    icon: Home,
  },
  {
    title: "Caixa de Entrada",
    href: "/inbox",
    icon: Inbox,
  },
  {
    title: "Caixa de Saída",
    href: "/sent",
    icon: Send,
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

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="p-4">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" className="h-9 w-9 shrink-0" asChild>
            <Link href="/dashboard">
              <Mail className="h-5 w-5" />
              <span className="sr-only">XMX MAIL</span>
            </Link>
          </Button>
          <span className="text-lg font-semibold tracking-tighter group-data-[collapsible=icon]:hidden">XMX MAIL</span>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {menuItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    asChild
                    isActive={pathname === item.href}
                    tooltip={{
                      children: item.title,
                    }}
                  >
                    <Link href={item.href}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter className="p-4 border-t">
        <div className="flex items-center justify-between">
          <div className="text-sm group-data-[collapsible=icon]:hidden">
            <p className="font-medium truncate">{user.email}</p>
            <p className="text-gray-500">
              {user.user_metadata?.username || 'Usuário'}
            </p>
          </div>
          <Button 
            variant="ghost" 
            size="icon"
            onClick={handleLogout}
            title="Sair"
            className="h-8 w-8"
          >
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}