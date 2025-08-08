"use client"

import { useEffect, useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Mail, Loader2, AlertCircle, ExternalLink, Shield } from "lucide-react"
import { Progress } from "@/components/ui/progress"

interface GmailAuthDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: () => void
  isAuthenticating: boolean
  error?: string | null
  autoOpen?: boolean // Se vai abrir automaticamente
}

export function GmailAuthDialog({
  open,
  onOpenChange,
  onConfirm,
  isAuthenticating,
  error,
  autoOpen = true
}: GmailAuthDialogProps) {
  const [countdown, setCountdown] = useState(3)
  const [hasStarted, setHasStarted] = useState(false)
  
  // Countdown para auto-abrir
  useEffect(() => {
    if (open && autoOpen && !hasStarted && !isAuthenticating) {
      setHasStarted(true)
      const timer = setInterval(() => {
        setCountdown(prev => {
          if (prev <= 1) {
            clearInterval(timer)
            onConfirm()
            return 0
          }
          return prev - 1
        })
      }, 1000)
      
      return () => clearInterval(timer)
    }
  }, [open, autoOpen, hasStarted, onConfirm, isAuthenticating])
  
  // Reset quando fechar
  useEffect(() => {
    if (!open) {
      setCountdown(3)
      setHasStarted(false)
    }
  }, [open])

  const progress = ((3 - countdown) / 3) * 100

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-950">
              {isAuthenticating ? (
                <Loader2 className="h-6 w-6 animate-spin text-blue-600 dark:text-blue-400" />
              ) : (
                <Mail className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              )}
            </div>
            <div>
              <DialogTitle>Conectar ao Gmail</DialogTitle>
              <DialogDescription>
                {isAuthenticating 
                  ? "Aguardando autorização..." 
                  : "Precisamos conectar sua conta do Gmail para acessar seus e-mails"
                }
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Erro */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Informações de segurança */}
          {!isAuthenticating && !error && (
            <div className="space-y-3">
              <div className="flex items-start gap-3 text-sm text-muted-foreground">
                <Shield className="h-4 w-4 mt-0.5 text-green-600 dark:text-green-400" />
                <div>
                  <p className="font-medium text-foreground">Conexão Segura</p>
                  <p>Suas credenciais são gerenciadas diretamente pelo Google. Não temos acesso à sua senha.</p>
                </div>
              </div>
              
              <div className="flex items-start gap-3 text-sm text-muted-foreground">
                <ExternalLink className="h-4 w-4 mt-0.5 text-blue-600 dark:text-blue-400" />
                <div>
                  <p className="font-medium text-foreground">Autorização OAuth 2.0</p>
                  <p>Uma nova janela será aberta para você autorizar o acesso no Google.</p>
                </div>
              </div>
            </div>
          )}

          {/* Progresso do countdown */}
          {autoOpen && !isAuthenticating && countdown > 0 && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Abrindo automaticamente em</span>
                <span className="font-medium">{countdown}s</span>
              </div>
              <Progress value={progress} className="h-2" />
            </div>
          )}

          {/* Status de autenticação */}
          {isAuthenticating && (
            <div className="flex items-center justify-center py-4">
              <div className="text-center space-y-2">
                <Loader2 className="h-8 w-8 animate-spin mx-auto text-blue-600 dark:text-blue-400" />
                <p className="text-sm text-muted-foreground">
                  Complete a autorização na janela que foi aberta...
                </p>
                <p className="text-xs text-muted-foreground">
                  Se a janela não abriu, verifique se popups estão bloqueados.
                </p>
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          {!isAuthenticating && (
            <>
              <Button
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                Cancelar
              </Button>
              <Button
                onClick={onConfirm}
                disabled={isAuthenticating}
              >
                {countdown > 0 && autoOpen ? (
                  <>Conectar Agora</>
                ) : (
                  <>Conectar ao Gmail</>
                )}
              </Button>
            </>
          )}
          
          {isAuthenticating && (
            <Button
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="w-full"
            >
              Cancelar
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}