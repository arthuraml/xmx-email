import Link from "next/link"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Mail } from "lucide-react"

export default function LoginPage() {
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
          <form className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">E-mail</Label>
              <Input id="email" type="email" placeholder="seu@email.com" required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Senha</Label>
              <Input id="password" type="password" required />
            </div>
            <Button type="submit" className="w-full" asChild>
              <Link href="/dashboard">Entrar</Link>
            </Button>
          </form>
        </div>
        <div className="text-center text-sm text-gray-500 dark:text-gray-400">
          Não tem uma conta?{" "}
          <Link href="#" className="font-medium text-primary hover:underline">
            Cadastre-se
          </Link>
        </div>
      </div>
    </div>
  )
}
