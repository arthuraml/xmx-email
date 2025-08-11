interface GmailMessage {
  id: string;
  threadId: string;
  from: string;
  to: string;
  subject: string;
  date: Date;
  snippet: string;
  body: string;
  isUnread: boolean;
  labels: string[];
}

interface GmailResponse {
  success: boolean;
  count?: number;
  messages?: GmailMessage[];
  message?: GmailMessage;
  error?: string;
}

export class GmailAPI {
  private static baseUrl = '/api/gmail';

  static async getInboxMessages(limit: number = 20): Promise<GmailResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/inbox?limit=${limit}`);
      return await response.json();
    } catch (error) {
      console.error('Error fetching inbox messages:', error);
      return { success: false, error: 'Failed to fetch inbox messages' };
    }
  }

  static async getSentMessages(limit: number = 20): Promise<GmailResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/sent?limit=${limit}`);
      return await response.json();
    } catch (error) {
      console.error('Error fetching sent messages:', error);
      return { success: false, error: 'Failed to fetch sent messages' };
    }
  }

  static async getMessageById(id: string): Promise<GmailResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/message/${id}`);
      return await response.json();
    } catch (error) {
      console.error('Error fetching message:', error);
      return { success: false, error: 'Failed to fetch message' };
    }
  }

  static async markAsRead(id: string): Promise<GmailResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/message/${id}/read`, {
        method: 'POST',
      });
      return await response.json();
    } catch (error) {
      console.error('Error marking message as read:', error);
      return { success: false, error: 'Failed to mark message as read' };
    }
  }

  static async processEmail(emailId: string): Promise<{
    success: boolean;
    email_id?: string;
    classification?: any;
    tracking_data?: any;
    generated_response?: any;
    error?: string;
  }> {
    try {
      const response = await fetch('/api/llm/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email_id: emailId }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to process email');
      }
      
      return data;
    } catch (error) {
      console.error('Error processing email:', error);
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Failed to process email' 
      };
    }
  }
}

export function formatEmailDate(date: Date | string): string {
  const emailDate = new Date(date);
  const now = new Date();
  const diffMs = now.getTime() - emailDate.getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffHours < 1) {
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    return `${diffMinutes} min atrás`;
  } else if (diffHours < 24) {
    return `${diffHours}h atrás`;
  } else if (diffDays < 7) {
    return `${diffDays}d atrás`;
  } else {
    return emailDate.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'short',
      year: emailDate.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    });
  }
}

export function truncateText(text: string, maxLength: number = 100): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength).trim() + '...';
}

export function extractEmailName(email: string): string {
  const match = email.match(/^"?(.+?)"?\s*<.+>$/);
  if (match) {
    return match[1];
  }
  const nameMatch = email.match(/^(.+?)@/);
  return nameMatch ? nameMatch[1] : email;
}