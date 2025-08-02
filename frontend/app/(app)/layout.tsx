import { redirect } from 'next/navigation'
import { createClient } from '@/utils/supabase/server'
import { SidebarProvider, SidebarTrigger, SidebarInset } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/app-sidebar"
import { cookies } from 'next/headers'

export default async function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const supabase = await createClient()
  
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) {
    redirect('/login')
  }

  const cookieStore = await cookies()
  const defaultOpen = cookieStore.get("sidebar:state")?.value === "true"

  return (
    <SidebarProvider defaultOpen={defaultOpen}>
      <div className="flex min-h-screen">
        <AppSidebar user={user} />
        <SidebarInset>
          <main className="p-4 md:p-6">
            <div className="md:hidden mb-4">
              <SidebarTrigger />
            </div>
            {children}
          </main>
        </SidebarInset>
      </div>
    </SidebarProvider>
  )
}