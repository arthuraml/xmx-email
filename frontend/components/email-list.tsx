"use client"

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { ScrollArea } from '@/components/ui/scroll-area'
import { formatEmailDate, truncateText, extractEmailName } from '@/lib/gmail'
import { Mail, Inbox } from 'lucide-react'

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
  emptyMessage?: string
}

export function EmailList({ 
  emails, 
  loading = false, 
  onEmailClick,
  emptyMessage = "Nenhum e-mail encontrado."
}: EmailListProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const handleEmailClick = (email: Email) => {
    setSelectedId(email.id)
    if (onEmailClick) {
      onEmailClick(email)
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
                <span className="text-xs text-muted-foreground">
                  {formatEmailDate(email.date)}
                </span>
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