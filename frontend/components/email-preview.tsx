"use client"

import { useState } from 'react'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { formatEmailDate, extractEmailName } from '@/lib/gmail'
import { ArrowLeft, Mail, Clock, Tag, User } from 'lucide-react'

interface EmailPreviewProps {
  email: {
    id: string
    from: string
    to: string
    subject: string
    body: string
    date: Date | string
    isUnread: boolean
    labels: string[]
  }
  onBack?: () => void
  onMarkAsRead?: (id: string) => void
}

export function EmailPreview({ email, onBack, onMarkAsRead }: EmailPreviewProps) {
  const [isMarking, setIsMarking] = useState(false)

  const handleMarkAsRead = async () => {
    if (onMarkAsRead && email.isUnread) {
      setIsMarking(true)
      await onMarkAsRead(email.id)
      setIsMarking(false)
    }
  }

  // Parse HTML body if needed
  const renderBody = () => {
    if (email.body.includes('<html>') || email.body.includes('<body>')) {
      return (
        <div 
          className="prose prose-sm max-w-none"
          dangerouslySetInnerHTML={{ __html: email.body }}
        />
      )
    }
    
    return (
      <div className="whitespace-pre-wrap font-mono text-sm">
        {email.body}
      </div>
    )
  }

  return (
    <Card className="h-full">
      <CardHeader className="space-y-4">
        <div className="flex items-center justify-between">
          {onBack && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onBack}
              className="gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Voltar
            </Button>
          )}
          
          {email.isUnread && onMarkAsRead && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleMarkAsRead}
              disabled={isMarking}
            >
              {isMarking ? 'Marcando...' : 'Marcar como lido'}
            </Button>
          )}
        </div>

        <div className="space-y-3">
          <h2 className="text-xl font-semibold">
            {email.subject || '(sem assunto)'}
          </h2>

          <div className="grid gap-2 text-sm">
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">De:</span>
              <span className="font-medium">{email.from}</span>
            </div>
            
            <div className="flex items-center gap-2">
              <Mail className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">Para:</span>
              <span>{email.to}</span>
            </div>
            
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">Data:</span>
              <span>{new Date(email.date).toLocaleString('pt-BR')}</span>
            </div>
          </div>

          {email.labels.length > 0 && (
            <div className="flex items-center gap-2">
              <Tag className="h-4 w-4 text-muted-foreground" />
              <div className="flex gap-1 flex-wrap">
                {email.labels
                  .filter(label => !['INBOX', 'SENT', 'UNREAD'].includes(label))
                  .map((label) => (
                    <Badge key={label} variant="secondary">
                      {label}
                    </Badge>
                  ))}
              </div>
            </div>
          )}
        </div>
      </CardHeader>

      <Separator />

      <CardContent className="pt-6">
        <div className="max-h-[400px] overflow-y-auto">
          {renderBody()}
        </div>
      </CardContent>
    </Card>
  )
}