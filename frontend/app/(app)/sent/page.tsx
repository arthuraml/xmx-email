"use client"

import { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { EmailList } from "@/components/email-list"
import { EmailPreview } from "@/components/email-preview"
import { GmailAuthDialog } from "@/components/gmail-auth-dialog"
import { GmailAPI } from "@/lib/gmail"
import { useGmailAuth } from "@/lib/hooks/use-gmail-auth"
import { RefreshCw, Mail, AlertCircle, Loader2 } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"

interface Email {
  id: string
  from: string
  to: string
  subject: string
  snippet: string
  body: string
  date: Date | string
  isUnread: boolean
  labels: string[]
}

export default function SentPage() {
  const [emails, setEmails] = useState<Email[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  
  // Hook de autenticação Gmail
  const {
    isAuthenticated,
    isChecking,
    authError,
    userEmail,
    isAuthenticating,
    showAuthDialog,
    startAuth,
    cancelAuthDialog,
    checkAuthStatus
  } = useGmailAuth({
    autoAuth: true,
    showDialog: true,
    onAuthSuccess: (email) => {
      // Recarregar emails após autenticação bem-sucedida
      fetchEmails()
    },
    onAuthError: (error) => {
      setError(`Erro na autenticação: ${error}`)
    }
  })

  const fetchEmails = async () => {
    try {
      setError(null)
      const response = await GmailAPI.getSentMessages(50)
      
      if (!response.success) {
        // Verificar se é erro de autenticação
        if (response.error?.includes('Gmail not connected') || response.error?.includes('authenticate')) {
          // O hook já deve cuidar disso automaticamente
          setError('Conecte sua conta do Gmail para ver seus e-mails enviados')
          return
        }
        throw new Error(response.error || 'Failed to fetch emails')
      }
      
      setEmails(response.messages || [])
    } catch (err) {
      console.error('Error fetching sent messages:', err)
      setError(err instanceof Error ? err.message : 'Failed to load emails')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    // Só buscar emails se estiver autenticado
    if (isAuthenticated) {
      fetchEmails()
    } else if (!isChecking && !isAuthenticated) {
      setLoading(false)
    }
  }, [isAuthenticated, isChecking])

  const handleRefresh = () => {
    setRefreshing(true)
    fetchEmails()
  }

  const handleEmailClick = async (email: Email) => {
    // Fetch full email details
    const response = await GmailAPI.getMessageById(email.id)
    if (response.success && response.message) {
      setSelectedEmail(response.message)
    } else {
      setSelectedEmail(email)
    }
  }

  const handleBack = () => {
    setSelectedEmail(null)
  }

  // Mostrar loading enquanto verifica autenticação
  if (isChecking) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-96">
          <div className="text-center space-y-4">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
            <p className="text-muted-foreground">Verificando autenticação...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Mostrar estado de não autenticado
  if (!isAuthenticated && !loading) {
    return (
      <>
        <Card>
          <CardHeader>
            <CardTitle>Caixa de Saída</CardTitle>
            <CardDescription>Conecte sua conta do Gmail para acessar seus e-mails enviados</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center space-y-6 py-8">
              <div className="flex justify-center">
                <div className="flex h-20 w-20 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-950">
                  <Mail className="h-10 w-10 text-blue-600 dark:text-blue-400" />
                </div>
              </div>
              
              <div className="space-y-2">
                <h3 className="text-lg font-semibold">Gmail não conectado</h3>
                <p className="text-muted-foreground max-w-sm mx-auto">
                  Para acessar seus e-mails enviados, você precisa autorizar o acesso à sua conta do Gmail.
                </p>
              </div>

              {authError && (
                <Alert variant="destructive" className="max-w-md mx-auto">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{authError}</AlertDescription>
                </Alert>
              )}

              <Button 
                onClick={startAuth} 
                size="lg"
                disabled={isAuthenticating}
              >
                {isAuthenticating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Conectando...
                  </>
                ) : (
                  <>
                    <Mail className="mr-2 h-4 w-4" />
                    Conectar ao Gmail
                  </>
                )}
              </Button>

              <p className="text-xs text-muted-foreground">
                Usamos OAuth 2.0 para uma conexão segura. Suas credenciais são gerenciadas pelo Google.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Dialog de autenticação */}
        <GmailAuthDialog
          open={showAuthDialog}
          onOpenChange={cancelAuthDialog}
          onConfirm={startAuth}
          isAuthenticating={isAuthenticating}
          error={authError}
          autoOpen={true}
        />
      </>
    )
  }

  // Mostrar erro se houver
  if (error && !authError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Caixa de Saída</CardTitle>
          <CardDescription>Erro ao carregar emails</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center space-y-4">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
            <Button onClick={handleRefresh} variant="outline">
              Tentar novamente
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Mostrar preview de email se selecionado
  if (selectedEmail) {
    return (
      <EmailPreview
        email={selectedEmail}
        onBack={handleBack}
      />
    )
  }

  // Mostrar lista de emails
  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle>Caixa de Saída</CardTitle>
            <CardDescription>
              {loading ? 'Carregando...' : `${emails.length} emails enviados`}
              {userEmail && (
                <span className="ml-2 text-xs">• {userEmail}</span>
              )}
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={refreshing || loading}
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <EmailList
          emails={emails}
          loading={loading}
          onEmailClick={handleEmailClick}
          emptyMessage="Você ainda não enviou nenhum email."
        />
      </CardContent>
    </Card>
  )
}