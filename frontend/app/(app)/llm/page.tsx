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
  AlertCircle,
  DollarSign,
  TrendingUp,
  BarChart3,
  Calendar
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
  
  // Costs
  cost_total_brl?: number
  cost_total_usd?: number
  exchange_rate?: number
  total_tokens?: number
}

export default function LLMPage() {
  const [emails, setEmails] = useState<ProcessedEmail[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedEmail, setSelectedEmail] = useState<ProcessedEmail | null>(null)
  const [editingResponse, setEditingResponse] = useState(false)
  const [editedBody, setEditedBody] = useState('')
  const [activeTab, setActiveTab] = useState('all')
  const [processing, setProcessing] = useState(false)
  const [costSummary, setCostSummary] = useState<any>(null)
  const [dailyCosts, setDailyCosts] = useState<any>(null)
  const [productSummary, setProductSummary] = useState<any>(null)
  const [mainTab, setMainTab] = useState('emails')

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
  
  // Fetch cost analytics
  const fetchCostAnalytics = async () => {
    try {
      // Fetch cost summary
      const summaryResponse = await fetch('/api/llm/analytics/costs/summary?period=month', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (summaryResponse.ok) {
        const summaryData = await summaryResponse.json()
        setCostSummary(summaryData)
      }
      
      // Fetch daily costs
      const dailyResponse = await fetch('/api/llm/analytics/costs/daily?days=7', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (dailyResponse.ok) {
        const dailyData = await dailyResponse.json()
        setDailyCosts(dailyData)
      }
      
      // Fetch product summary
      const productResponse = await fetch('/api/llm/analytics/products/summary?period=all', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (productResponse.ok) {
        const productData = await productResponse.json()
        setProductSummary(productData)
      }
      
    } catch (error) {
      console.error('Error fetching cost analytics:', error)
    }
  }

  useEffect(() => {
    fetchProcessedEmails()
    fetchCostAnalytics()
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

      {/* Main Tabs */}
      <Tabs value={mainTab} onValueChange={setMainTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="emails">E-mails Processados</TabsTrigger>
          <TabsTrigger value="products">
            <Package className="h-4 w-4 mr-2" />
            Produtos
          </TabsTrigger>
          <TabsTrigger value="analytics">
            <DollarSign className="h-4 w-4 mr-2" />
            Custos e Análise
          </TabsTrigger>
        </TabsList>
        
        {/* Emails Tab */}
        <TabsContent value="emails">
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
                              {email.product_name ? (
                                <Badge variant="default" className="text-xs">
                                  {email.product_name}
                                </Badge>
                              ) : (
                                <Badge variant="secondary" className="text-xs">
                                  Sem produto
                                </Badge>
                              )}
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
                              {email.cost_total_brl && (
                                <Badge variant="outline" className="text-xs">
                                  R$ {email.cost_total_brl.toFixed(2)}
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
      </TabsContent>
      
      {/* Products Tab */}
      <TabsContent value="products" className="space-y-4">
        <div className="grid gap-4">
          {/* Products Overview */}
          <Card>
            <CardHeader>
              <CardTitle>Produtos Monitorados</CardTitle>
              <CardDescription>
                Sistema configurado para processar apenas e-mails relacionados aos produtos abaixo
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {productSummary?.products?.map((product: string) => (
                  <div key={product} className="p-3 border rounded-lg">
                    <div className="font-medium">{product}</div>
                    <div className="text-sm text-muted-foreground mt-1">
                      {productSummary?.statistics?.[product]?.count || 0} emails
                    </div>
                    {productSummary?.statistics?.[product]?.cost_brl > 0 && (
                      <div className="text-xs text-muted-foreground">
                        R$ {productSummary.statistics[product].cost_brl.toFixed(2)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Product Statistics */}
          {productSummary && (
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Estatísticas por Produto</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(productSummary.statistics).map(([product, stats]: [string, any]) => (
                      <div key={product} className="flex justify-between items-center">
                        <div>
                          <div className="font-medium">{product}</div>
                          <div className="text-xs text-muted-foreground">
                            {stats.support_count} suporte | {stats.tracking_count} rastreamento
                          </div>
                        </div>
                        <div className="text-right">
                          <Badge variant={product === "Sem Produto" ? "secondary" : "default"}>
                            {stats.count} emails
                          </Badge>
                          {stats.with_response > 0 && (
                            <div className="text-xs text-green-600 mt-1">
                              {stats.with_response} com resposta
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Economia Potencial</CardTitle>
                  <CardDescription>
                    Custos evitáveis com validação de produtos
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <div className="text-sm text-muted-foreground">Emails sem produto</div>
                      <div className="text-2xl font-bold">
                        {productSummary?.summary?.emails_without_product || 0}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Economia potencial</div>
                      <div className="text-2xl font-bold text-green-600">
                        R$ {productSummary?.summary?.potential_savings_brl?.toFixed(2) || "0.00"}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Taxa de cobertura</div>
                      <div className="text-lg font-semibold">
                        {productSummary?.summary?.product_coverage_rate?.toFixed(1) || 0}%
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </TabsContent>
      
      {/* Analytics Tab */}
      <TabsContent value="analytics" className="space-y-4">
        <div className="grid gap-4 md:grid-cols-3">
          {/* Cost Summary Cards */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                Custo Total (Mês)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                R$ {costSummary?.costs?.combined?.total_brl?.toFixed(2) || '0.00'}
              </div>
              <p className="text-xs text-muted-foreground">
                {costSummary?.costs?.combined?.total_operations || 0} operações
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                Custo Médio por E-mail
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                R$ {costSummary?.averages?.cost_per_email_brl?.toFixed(2) || '0.00'}
              </div>
              <p className="text-xs text-muted-foreground">
                {costSummary?.averages?.tokens_per_email || 0} tokens/email
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                Taxa de Câmbio
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                R$ {costSummary?.current_exchange_rate?.toFixed(2) || '0.00'}
              </div>
              <p className="text-xs text-muted-foreground">
                1 USD = R$ {costSummary?.current_exchange_rate?.toFixed(2) || '0.00'}
              </p>
            </CardContent>
          </Card>
        </div>
        
        {/* Daily Costs Chart */}
        {dailyCosts && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">
                <BarChart3 className="h-5 w-5 inline mr-2" />
                Custos Diários (Últimos 7 dias)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {dailyCosts.daily?.map((day: any) => (
                  <div key={day.date} className="flex items-center justify-between p-2 hover:bg-muted/50 rounded">
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">
                        {new Date(day.date).toLocaleDateString('pt-BR', { 
                          weekday: 'short', 
                          day: '2-digit', 
                          month: 'short' 
                        })}
                      </span>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-sm text-muted-foreground">
                        {day.count} emails
                      </span>
                      <span className="font-medium">
                        R$ {day.cost_brl.toFixed(2)}
                      </span>
                    </div>
                  </div>
                ))}
                <div className="border-t pt-2 mt-2 flex justify-between">
                  <span className="font-medium">Total</span>
                  <span className="font-bold">
                    R$ {dailyCosts.totals?.cost_brl?.toFixed(2) || '0.00'}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
        
        {/* Token Usage */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              <TrendingUp className="h-5 w-5 inline mr-2" />
              Uso de Tokens
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <p className="text-sm font-medium">Entrada</p>
                <p className="text-2xl font-bold">
                  {costSummary?.tokens?.input?.toLocaleString() || 0}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium">Saída</p>
                <p className="text-2xl font-bold">
                  {costSummary?.tokens?.output?.toLocaleString() || 0}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium">Pensamento</p>
                <p className="text-2xl font-bold">
                  {costSummary?.tokens?.thinking?.toLocaleString() || 0}
                </p>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t">
              <div className="flex justify-between">
                <span className="text-sm font-medium">Total de Tokens</span>
                <span className="font-bold">
                  {costSummary?.tokens?.total?.toLocaleString() || 0}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
    </div>
  )
}