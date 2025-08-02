import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"

export default function DashboardPage() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Dashboard</h1>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Bem-vindo!</CardTitle>
            <CardDescription>Este é o seu painel principal do XMX MAIL.</CardDescription>
          </CardHeader>
          <CardContent>
            <p>Use a navegação à esquerda para acessar sua caixa de entrada e de saída.</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Novos E-mails</CardTitle>
            <CardDescription>Resumo dos seus e-mails não lidos.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">12</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>E-mails Enviados</CardTitle>
            <CardDescription>Total de e-mails enviados este mês.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">84</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
