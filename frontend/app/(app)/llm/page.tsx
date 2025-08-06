"use client"

import { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Textarea } from "@/components/ui/textarea"
import { 
  RefreshCw, 
  Send, 
  Check, 
  X, 
  Edit, 
  Package, 
  HelpCircle,
  Clock,
  AlertCircle
} from "lucide-react"

interface ProcessedEmail {
  email_id: string
  from_address: string
  to_address: string
  subject: string
  body: string
  received_at: string
  
  // Classification
  is_support: boolean
  is_tracking: boolean
  classification_type: 'support' | 'tracking' | 'both' | 'none'
  urgency: 'high' | 'medium' | 'low'
  confidence: number
  
  // Response
  suggested_subject?: string
  suggested_body?: string
  response_tone?: string
  requires_followup?: boolean
  
  // Tracking
  tracking_data?: {
    order_id: string
    tracking_code: string
    status: string
    last_location?: string
  }
  
  // Status
  response_approved?: boolean
  response_sent?: boolean
  processed_at: string
}

export default function LLMPage() {
  const [emails, setEmails] = useState<ProcessedEmail[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedEmail, setSelectedEmail] = useState<ProcessedEmail | null>(null)
  const [editingResponse, setEditingResponse] = useState(false)
  const [editedBody, setEditedBody] = useState('')
  const [activeTab, setActiveTab] = useState('all')
  const [processing, setProcessing] = useState(false)

  // Fetch processed emails
  const fetchProcessedEmails = async () => {
    try {
      setLoading(true)
      
      // Fetch from Python backend via Node.js proxy
      const response = await fetch('/api/llm/processed', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch processed emails')
      }
      
      const data = await response.json()
      setEmails(data.emails || [])
      
    } catch (error) {
      console.error('Error fetching processed emails:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProcessedEmails()
  }, [])

  // Filter emails based on tab
  const filteredEmails = emails.filter(email => {
    if (activeTab === 'all') return true
    if (activeTab === 'support') return email.is_support
    if (activeTab === 'tracking') return email.is_tracking
    if (activeTab === 'pending') return !email.response_sent
    if (activeTab === 'sent') return email.response_sent
    return true
  })

  // Process new email
  const processEmail = async (emailId: string) => {
    setProcessing(true)
    try {
      const response = await fetch('/api/llm/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email_id: emailId })
      })
      
      if (response.ok) {
        await fetchProcessedEmails()
      }
    } catch (error) {
      console.error('Error processing email:', error)
    } finally {
      setProcessing(false)
    }
  }

  // Approve response
  const approveResponse = async (emailId: string) => {
    try {
      const response = await fetch('/api/llm/approve', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          email_id: emailId,
          body: editingResponse ? editedBody : undefined
        })
      })
      
      if (response.ok) {
        setEditingResponse(false)
        await fetchProcessedEmails()
      }
    } catch (error) {
      console.error('Error approving response:', error)
    }
  }

  // Send response
  const sendResponse = async (emailId: string) => {
    try {
      const response = await fetch('/api/llm/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email_id: emailId })
      })
      
      if (response.ok) {
        await fetchProcessedEmails()
      }
    } catch (error) {
      console.error('Error sending response:', error)
    }
  }

  // Get classification icon
  const getClassificationIcon = (type: string) => {
    switch (type) {
      case 'support':
        return <HelpCircle className="h-4 w-4" />
      case 'tracking':
        return <Package className="h-4 w-4" />
      case 'both':
        return (
          <div className="flex gap-1">
            <HelpCircle className="h-4 w-4" />
            <Package className="h-4 w-4" />
          </div>
        )
      default:
        return null
    }
  }

  // Get urgency color
  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'high':
        return 'destructive'
      case 'medium':
        return 'default'
      case 'low':
        return 'secondary'
      default:
        return 'outline'
    }
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-96">
          <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle>Processamento LLM</CardTitle>
              <CardDescription>
                E-mails processados e respostas sugeridas pela IA
              </CardDescription>
            </div>
            <Button 
              onClick={fetchProcessedEmails}
              variant="outline"
              size="sm"
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Atualizar
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="all">
            Todos ({emails.length})
          </TabsTrigger>
          <TabsTrigger value="support">
            Suporte ({emails.filter(e => e.is_support).length})
          </TabsTrigger>
          <TabsTrigger value="tracking">
            Rastreamento ({emails.filter(e => e.is_tracking).length})
          </TabsTrigger>
          <TabsTrigger value="pending">
            Pendentes ({emails.filter(e => !e.response_sent).length})
          </TabsTrigger>
          <TabsTrigger value="sent">
            Enviados ({emails.filter(e => e.response_sent).length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {/* Email List */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">E-mails Processados</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <ScrollArea className="h-[600px]">
                  <div className="space-y-2 p-4">
                    {filteredEmails.map((email) => (
                      <Card 
                        key={email.email_id}
                        className={`cursor-pointer transition-colors ${
                          selectedEmail?.email_id === email.email_id 
                            ? 'border-primary' 
                            : 'hover:bg-muted/50'
                        }`}
                        onClick={() => {
                          setSelectedEmail(email)
                          setEditingResponse(false)
                          setEditedBody(email.suggested_body || '')
                        }}
                      >
                        <CardContent className="p-4">
                          <div className="space-y-2">
                            {/* Header */}
                            <div className="flex justify-between items-start">
                              <div className="flex-1">
                                <p className="font-medium text-sm truncate">
                                  {email.from_address}
                                </p>
                                <p className="text-sm text-muted-foreground truncate">
                                  {email.subject}
                                </p>
                              </div>
                              <div className="flex gap-2">
                                {getClassificationIcon(email.classification_type)}
                                {email.response_sent && (
                                  <Check className="h-4 w-4 text-green-600" />
                                )}
                              </div>
                            </div>

                            {/* Badges */}
                            <div className="flex gap-2 flex-wrap">
                              <Badge variant={getUrgencyColor(email.urgency)} className="text-xs">
                                {email.urgency}
                              </Badge>
                              {email.is_support && (
                                <Badge variant="outline" className="text-xs">
                                  Suporte
                                </Badge>
                              )}
                              {email.is_tracking && (
                                <Badge variant="outline" className="text-xs">
                                  Rastreamento
                                </Badge>
                              )}
                              {email.confidence && (
                                <Badge variant="secondary" className="text-xs">
                                  {(email.confidence * 100).toFixed(0)}%
                                </Badge>
                              )}
                            </div>

                            {/* Tracking Info */}
                            {email.tracking_data && (
                              <div className="text-xs text-muted-foreground">
                                📦 {email.tracking_data.order_id} - {email.tracking_data.status}
                              </div>
                            )}

                            {/* Time */}
                            <div className="flex items-center gap-1 text-xs text-muted-foreground">
                              <Clock className="h-3 w-3" />
                              {new Date(email.received_at).toLocaleString('pt-BR')}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>

            {/* Email Details & Response */}
            {selectedEmail ? (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Detalhes e Resposta</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Original Email */}
                  <div className="space-y-2">
                    <h4 className="font-medium text-sm">E-mail Original</h4>
                    <div className="rounded-lg bg-muted p-3 text-sm">
                      <p className="font-medium">{selectedEmail.subject}</p>
                      <p className="text-muted-foreground mt-2">
                        {selectedEmail.body}
                      </p>
                    </div>
                  </div>

                  {/* Classification Details */}
                  <div className="space-y-2">
                    <h4 className="font-medium text-sm">Classificação</h4>
                    <div className="flex gap-2 flex-wrap">
                      <Badge>{selectedEmail.classification_type}</Badge>
                      <Badge variant="outline">
                        Urgência: {selectedEmail.urgency}
                      </Badge>
                      <Badge variant="secondary">
                        Confiança: {(selectedEmail.confidence * 100).toFixed(0)}%
                      </Badge>
                    </div>
                  </div>

                  {/* Tracking Data */}
                  {selectedEmail.tracking_data && (
                    <div className="space-y-2">
                      <h4 className="font-medium text-sm">Dados de Rastreamento</h4>
                      <div className="rounded-lg bg-muted p-3 text-sm space-y-1">
                        <p><strong>Pedido:</strong> {selectedEmail.tracking_data.order_id}</p>
                        <p><strong>Código:</strong> {selectedEmail.tracking_data.tracking_code}</p>
                        <p><strong>Status:</strong> {selectedEmail.tracking_data.status}</p>
                        {selectedEmail.tracking_data.last_location && (
                          <p><strong>Localização:</strong> {selectedEmail.tracking_data.last_location}</p>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Suggested Response */}
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <h4 className="font-medium text-sm">Resposta Sugerida</h4>
                      {!selectedEmail.response_sent && (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setEditingResponse(!editingResponse)}
                        >
                          <Edit className="h-4 w-4 mr-1" />
                          {editingResponse ? 'Cancelar' : 'Editar'}
                        </Button>
                      )}
                    </div>
                    
                    {selectedEmail.suggested_subject && (
                      <div className="text-sm">
                        <strong>Assunto:</strong> {selectedEmail.suggested_subject}
                      </div>
                    )}
                    
                    {editingResponse ? (
                      <Textarea
                        value={editedBody}
                        onChange={(e) => setEditedBody(e.target.value)}
                        className="min-h-[200px]"
                      />
                    ) : (
                      <div className="rounded-lg bg-muted p-3 text-sm whitespace-pre-wrap">
                        {selectedEmail.suggested_body || 'Nenhuma resposta sugerida'}
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  {!selectedEmail.response_sent && (
                    <div className="flex gap-2">
                      <Button
                        onClick={() => approveResponse(selectedEmail.email_id)}
                        className="flex-1"
                        variant="outline"
                      >
                        <Check className="h-4 w-4 mr-2" />
                        Aprovar
                      </Button>
                      <Button
                        onClick={() => sendResponse(selectedEmail.email_id)}
                        className="flex-1"
                      >
                        <Send className="h-4 w-4 mr-2" />
                        Enviar
                      </Button>
                    </div>
                  )}

                  {selectedEmail.response_sent && (
                    <div className="flex items-center gap-2 text-green-600">
                      <Check className="h-4 w-4" />
                      <span className="text-sm">Resposta enviada</span>
                    </div>
                  )}

                  {selectedEmail.requires_followup && (
                    <div className="flex items-center gap-2 text-amber-600">
                      <AlertCircle className="h-4 w-4" />
                      <span className="text-sm">Requer acompanhamento</span>
                    </div>
                  )}
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="flex items-center justify-center h-[600px] text-muted-foreground">
                  Selecione um e-mail para ver os detalhes
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}