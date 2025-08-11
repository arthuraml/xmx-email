"use client"

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { ScrollArea } from '@/components/ui/scroll-area'
import { formatEmailDate, truncateText, extractEmailName } from '@/lib/gmail'
import { Mail, Inbox, Cpu, Loader2 } from 'lucide-react'

interface Email {
  id: string
  from: string
  to: string
  subject: string
  snippet: string
  date: Date | string
  isUnread: boolean
  labels: string[]
}

interface EmailListProps {
  emails: Email[]
  loading?: boolean
  onEmailClick?: (email: Email) => void
  onProcessEmail?: (emailId: string) => Promise<void>
  emptyMessage?: string
}

export function EmailList({ 
  emails, 
  loading = false, 
  onEmailClick,
  onProcessEmail,
  emptyMessage = "Nenhum e-mail encontrado."
}: EmailListProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [processingIds, setProcessingIds] = useState<Set<string>>(new Set())

  const handleEmailClick = (email: Email) => {
    setSelectedId(email.id)
    if (onEmailClick) {
      onEmailClick(email)
    }
  }

  const handleProcessClick = async (e: React.MouseEvent, emailId: string) => {
    e.stopPropagation() // Prevent card click
    
    if (!onProcessEmail || processingIds.has(emailId)) return
    
    setProcessingIds(prev => new Set(prev).add(emailId))
    
    try {
      await onProcessEmail(emailId)
    } finally {
      setProcessingIds(prev => {
        const newSet = new Set(prev)
        newSet.delete(emailId)
        return newSet
      })
    }
  }

  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <Card key={i} className="p-4">
            <div className="space-y-2">
              <div className="flex justify-between items-start">
                <Skeleton className="h-5 w-48" />
                <Skeleton className="h-4 w-16" />
              </div>
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-full" />
            </div>
          </Card>
        ))}
      </div>
    )
  }

  if (emails.length === 0) {
    return (
      <Card className="p-12">
        <div className="flex flex-col items-center justify-center text-center space-y-3">
          <Inbox className="h-12 w-12 text-muted-foreground" />
          <p className="text-muted-foreground">{emptyMessage}</p>
        </div>
      </Card>
    )
  }

  return (
    <ScrollArea className="h-[600px]">
      <div className="space-y-2 pr-4">
        {emails.map((email) => (
          <Card
            key={email.id}
            className={`p-4 cursor-pointer transition-all hover:shadow-md ${
              selectedId === email.id ? 'border-primary' : ''
            } ${email.isUnread ? 'bg-accent/5' : ''}`}
            onClick={() => handleEmailClick(email)}
          >
            <div className="space-y-2">
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-2">
                  {email.isUnread && (
                    <div className="w-2 h-2 bg-primary rounded-full" />
                  )}
                  <span className={`text-sm ${email.isUnread ? 'font-semibold' : ''}`}>
                    {extractEmailName(email.from)}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {onProcessEmail && (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={(e) => handleProcessClick(e, email.id)}
                      disabled={processingIds.has(email.id)}
                      className="h-7 px-2"
                      title="Processar e-mail com IA"
                    >
                      {processingIds.has(email.id) ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Cpu className="h-3.5 w-3.5" />
                      )}
                      <span className="ml-1 text-xs">Processar</span>
                    </Button>
                  )}
                  <span className="text-xs text-muted-foreground">
                    {formatEmailDate(email.date)}
                  </span>
                </div>
              </div>
              
              <h4 className={`text-sm ${email.isUnread ? 'font-medium' : ''} line-clamp-1`}>
                {email.subject || '(sem assunto)'}
              </h4>
              
              <p className="text-sm text-muted-foreground line-clamp-2">
                {truncateText(email.snippet, 150)}
              </p>

              {email.labels.length > 0 && (
                <div className="flex gap-1 flex-wrap pt-1">
                  {email.labels
                    .filter(label => !['INBOX', 'SENT', 'UNREAD'].includes(label))
                    .slice(0, 3)
                    .map((label) => (
                      <Badge key={label} variant="secondary" className="text-xs">
                        {label}
                      </Badge>
                    ))}
                </div>
              )}
            </div>
          </Card>
        ))}
      </div>
    </ScrollArea>
  )
}