"use client"

import { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { EmailList } from "@/components/email-list"
import { EmailPreview } from "@/components/email-preview"
import { GmailAPI } from "@/lib/gmail"
import { RefreshCw } from "lucide-react"

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

  const fetchEmails = async () => {
    try {
      setError(null)
      const response = await GmailAPI.getSentMessages(50)
      
      if (!response.success) {
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
    fetchEmails()
  }, [])

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

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Caixa de Saída</CardTitle>
          <CardDescription>Erro ao carregar emails</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center space-y-4">
            <p className="text-red-500">{error}</p>
            <Button onClick={handleRefresh} variant="outline">
              Tentar novamente
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (selectedEmail) {
    return (
      <EmailPreview
        email={selectedEmail}
        onBack={handleBack}
      />
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle>Caixa de Saída</CardTitle>
            <CardDescription>
              {loading ? 'Carregando...' : `${emails.length} emails enviados`}
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={refreshing}
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