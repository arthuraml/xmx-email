"use client"

import { useState, useEffect, useCallback, useRef } from 'react'
import { toast } from 'sonner'

export interface GmailAuthStatus {
  isAuthenticated: boolean
  isChecking: boolean
  authError: string | null
  userEmail: string | null
}

export interface UseGmailAuthOptions {
  autoAuth?: boolean // Se deve abrir popup automaticamente
  onAuthSuccess?: (email: string) => void
  onAuthError?: (error: string) => void
  showDialog?: boolean // Se deve mostrar dialog antes do popup
}

export function useGmailAuth(options: UseGmailAuthOptions = {}) {
  const {
    autoAuth = true,
    onAuthSuccess,
    onAuthError,
    showDialog = true
  } = options

  const [status, setStatus] = useState<GmailAuthStatus>({
    isAuthenticated: false,
    isChecking: true,
    authError: null,
    userEmail: null
  })

  const [isAuthenticating, setIsAuthenticating] = useState(false)
  const [showAuthDialog, setShowAuthDialog] = useState(false)
  const authWindowRef = useRef<Window | null>(null)
  const hasTriedAutoAuth = useRef(false)

  // Verificar status de autenticação
  const checkAuthStatus = useCallback(async () => {
    try {
      setStatus(prev => ({ ...prev, isChecking: true, authError: null }))
      
      const response = await fetch('/api/auth/google/status', {
        method: 'GET',
        credentials: 'include'
      })
      
      const data = await response.json()
      
      if (data.authenticated) {
        setStatus({
          isAuthenticated: true,
          isChecking: false,
          authError: null,
          userEmail: data.email
        })
        return true
      } else {
        setStatus({
          isAuthenticated: false,
          isChecking: false,
          authError: null,
          userEmail: null
        })
        return false
      }
    } catch (error) {
      console.error('Error checking auth status:', error)
      setStatus(prev => ({
        ...prev,
        isChecking: false,
        authError: 'Erro ao verificar autenticação'
      }))
      return false
    }
  }, [])

  // Abrir popup de autenticação
  const openAuthPopup = useCallback(async () => {
    try {
      setIsAuthenticating(true)
      
      // Obter URL de autenticação
      const response = await fetch('/api/auth/google', {
        method: 'POST',
        credentials: 'include'
      })
      
      const data = await response.json()
      
      if (!data.success || !data.authUrl) {
        throw new Error(data.error || 'Failed to get auth URL')
      }
      
      // Configurações da janela popup
      const width = 500
      const height = 600
      const left = window.screenX + (window.outerWidth - width) / 2
      const top = window.screenY + (window.outerHeight - height) / 2
      
      // Abrir popup
      const authWindow = window.open(
        data.authUrl,
        'gmail-auth',
        `width=${width},height=${height},left=${left},top=${top},toolbar=no,menubar=no`
      )
      
      if (!authWindow) {
        throw new Error('Popup foi bloqueado. Por favor, permita popups para este site.')
      }
      
      authWindowRef.current = authWindow
      
      // Monitorar o popup
      const checkInterval = setInterval(() => {
        if (authWindow.closed) {
          clearInterval(checkInterval)
          setIsAuthenticating(false)
          authWindowRef.current = null
          // Verificar se autenticou após fechar
          checkAuthStatus()
        }
      }, 500)
      
      // Limpar intervalo após timeout
      setTimeout(() => {
        clearInterval(checkInterval)
        if (authWindowRef.current && !authWindowRef.current.closed) {
          authWindowRef.current.close()
        }
        setIsAuthenticating(false)
      }, 300000) // 5 minutos timeout
      
    } catch (error: any) {
      console.error('Error opening auth popup:', error)
      setIsAuthenticating(false)
      toast.error(error.message || 'Erro ao abrir janela de autenticação')
      onAuthError?.(error.message)
    }
  }, [checkAuthStatus, onAuthError])

  // Listener para mensagens do popup
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      // Verificar origem
      if (event.origin !== window.location.origin) return
      
      if (event.data.type === 'auth-success') {
        // Fechar popup se ainda estiver aberto
        if (authWindowRef.current && !authWindowRef.current.closed) {
          authWindowRef.current.close()
        }
        
        // Atualizar status
        setStatus({
          isAuthenticated: true,
          isChecking: false,
          authError: null,
          userEmail: event.data.email
        })
        
        setIsAuthenticating(false)
        setShowAuthDialog(false)
        
        toast.success('Gmail conectado com sucesso!')
        onAuthSuccess?.(event.data.email)
      } else if (event.data.type === 'auth-error') {
        setIsAuthenticating(false)
        setShowAuthDialog(false)
        
        const errorMsg = event.data.error || 'Erro na autenticação'
        setStatus(prev => ({ ...prev, authError: errorMsg }))
        
        toast.error(errorMsg)
        onAuthError?.(errorMsg)
      }
    }
    
    window.addEventListener('message', handleMessage)
    return () => window.removeEventListener('message', handleMessage)
  }, [onAuthSuccess, onAuthError])

  // Verificar autenticação ao montar
  useEffect(() => {
    checkAuthStatus().then(isAuth => {
      // Se não está autenticado e autoAuth está ativado
      if (!isAuth && autoAuth && !hasTriedAutoAuth.current) {
        hasTriedAutoAuth.current = true
        
        if (showDialog) {
          // Mostrar dialog antes
          setShowAuthDialog(true)
          // Abrir popup após 2 segundos
          setTimeout(() => {
            openAuthPopup()
          }, 2000)
        } else {
          // Abrir popup diretamente
          openAuthPopup()
        }
      }
    })
  }, []) // Apenas na montagem

  // Função para iniciar autenticação manualmente
  const startAuth = useCallback(() => {
    if (showDialog) {
      setShowAuthDialog(true)
      setTimeout(() => {
        openAuthPopup()
      }, 1500)
    } else {
      openAuthPopup()
    }
  }, [openAuthPopup, showDialog])

  // Função para cancelar dialog
  const cancelAuthDialog = useCallback(() => {
    setShowAuthDialog(false)
  }, [])

  return {
    ...status,
    isAuthenticating,
    showAuthDialog,
    checkAuthStatus,
    startAuth,
    cancelAuthDialog,
    openAuthPopup
  }
}