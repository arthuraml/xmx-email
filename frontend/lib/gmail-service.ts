import { gmail_v1 } from 'googleapis';
import { googleAuth } from './google-auth';

export interface EmailMessage {
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

export interface EmailBody {
  text: string;
  html: string;
}

// Simple in-memory cache implementation
class CacheService {
  private cache: Map<string, { data: any; expires: number }> = new Map();
  private ttl: number; // in milliseconds

  constructor(ttlSeconds: number = 300) {
    this.ttl = ttlSeconds * 1000;
  }

  get(key: string): any | null {
    const item = this.cache.get(key);
    
    if (!item) {
      return null;
    }

    if (Date.now() > item.expires) {
      this.cache.delete(key);
      return null;
    }

    return item.data;
  }

  set(key: string, data: any): void {
    this.cache.set(key, {
      data,
      expires: Date.now() + this.ttl
    });
  }

  delete(key: string): void {
    this.cache.delete(key);
  }

  clear(): void {
    this.cache.clear();
  }
}

export class GmailService {
  private cache: CacheService;

  constructor() {
    // Cache for 5 minutes by default
    this.cache = new CacheService(300);
  }

  private async getGmailClient(userEmail: string): Promise<gmail_v1.Gmail> {
    return googleAuth.getGmailClient(userEmail);
  }

  async listMessages(
    userEmail: string, 
    query: string, 
    maxResults: number = 20
  ): Promise<EmailMessage[]> {
    const cacheKey = `messages_${userEmail}_${query}_${maxResults}`;
    const cached = this.cache.get(cacheKey);
    
    if (cached) {
      return cached;
    }

    try {
      const gmail = await this.getGmailClient(userEmail);
      
      // Get message IDs
      const response = await gmail.users.messages.list({
        userId: 'me',
        q: query,
        maxResults: maxResults
      });

      if (!response.data.messages || response.data.messages.length === 0) {
        return [];
      }

      // Fetch full message details for each message
      const messages = await Promise.all(
        response.data.messages.map(async (message) => {
          try {
            if (!message.id) return null;
            const details = await this.getMessageDetails(userEmail, message.id);
            return details;
          } catch (error) {
            console.error(`Error fetching message ${message.id}:`, error);
            return null;
          }
        })
      );

      const validMessages = messages.filter((msg): msg is EmailMessage => msg !== null);
      this.cache.set(cacheKey, validMessages);
      
      return validMessages;
    } catch (error) {
      console.error('Error listing messages:', error);
      throw error;
    }
  }

  async getMessageDetails(userEmail: string, messageId: string): Promise<EmailMessage> {
    const cacheKey = `message_${userEmail}_${messageId}`;
    const cached = this.cache.get(cacheKey);
    
    if (cached) {
      return cached;
    }

    try {
      const gmail = await this.getGmailClient(userEmail);
      
      const response = await gmail.users.messages.get({
        userId: 'me',
        id: messageId
      });

      const message = response.data;
      const headers = message.payload?.headers || [];
      
      // Extract relevant headers
      const from = this.getHeader(headers, 'From');
      const to = this.getHeader(headers, 'To');
      const subject = this.getHeader(headers, 'Subject');
      const date = this.getHeader(headers, 'Date');
      
      // Extract body
      const body = this.extractBody(message.payload);
      
      const formattedMessage: EmailMessage = {
        id: message.id || '',
        threadId: message.threadId || '',
        from,
        to,
        subject,
        date: new Date(date),
        snippet: message.snippet || '',
        body: body.text || body.html || '',
        isUnread: message.labelIds?.includes('UNREAD') || false,
        labels: message.labelIds || []
      };

      this.cache.set(cacheKey, formattedMessage);
      
      return formattedMessage;
    } catch (error) {
      console.error('Error getting message details:', error);
      throw error;
    }
  }

  private getHeader(headers: gmail_v1.Schema$MessagePartHeader[], name: string): string {
    const header = headers.find(h => h.name?.toLowerCase() === name.toLowerCase());
    return header?.value || '';
  }

  private extractBody(payload?: gmail_v1.Schema$MessagePart): EmailBody {
    let textBody = '';
    let htmlBody = '';

    const extractFromParts = (parts?: gmail_v1.Schema$MessagePart[]) => {
      if (!parts) return;

      for (const part of parts) {
        if (part.mimeType === 'text/plain' && part.body?.data) {
          textBody = Buffer.from(part.body.data, 'base64').toString('utf-8');
        } else if (part.mimeType === 'text/html' && part.body?.data) {
          htmlBody = Buffer.from(part.body.data, 'base64').toString('utf-8');
        } else if (part.parts) {
          extractFromParts(part.parts);
        }
      }
    };

    if (!payload) {
      return { text: textBody, html: htmlBody };
    }

    // Check if body is directly in payload
    if (payload.body?.data) {
      if (payload.mimeType === 'text/plain') {
        textBody = Buffer.from(payload.body.data, 'base64').toString('utf-8');
      } else if (payload.mimeType === 'text/html') {
        htmlBody = Buffer.from(payload.body.data, 'base64').toString('utf-8');
      }
    }

    // Extract from parts
    if (payload.parts) {
      extractFromParts(payload.parts);
    }

    return { text: textBody, html: htmlBody };
  }

  async getInboxMessages(userEmail: string, maxResults: number = 20): Promise<EmailMessage[]> {
    return this.listMessages(userEmail, 'in:inbox', maxResults);
  }

  async getSentMessages(userEmail: string, maxResults: number = 20): Promise<EmailMessage[]> {
    return this.listMessages(userEmail, 'in:sent', maxResults);
  }

  async markAsRead(userEmail: string, messageId: string): Promise<boolean> {
    try {
      const gmail = await this.getGmailClient(userEmail);
      
      await gmail.users.messages.modify({
        userId: 'me',
        id: messageId,
        requestBody: {
          removeLabelIds: ['UNREAD']
        }
      });
      
      // Clear cache for this message
      this.cache.delete(`message_${userEmail}_${messageId}`);
      
      // Also clear list caches that might contain this message
      // This is a simple approach - clear all inbox caches
      this.clearInboxCache(userEmail);
      
      return true;
    } catch (error) {
      console.error('Error marking message as read:', error);
      throw error;
    }
  }

  async markAsUnread(userEmail: string, messageId: string): Promise<boolean> {
    try {
      const gmail = await this.getGmailClient(userEmail);
      
      await gmail.users.messages.modify({
        userId: 'me',
        id: messageId,
        requestBody: {
          addLabelIds: ['UNREAD']
        }
      });
      
      // Clear cache for this message
      this.cache.delete(`message_${userEmail}_${messageId}`);
      
      // Also clear list caches
      this.clearInboxCache(userEmail);
      
      return true;
    } catch (error) {
      console.error('Error marking message as unread:', error);
      throw error;
    }
  }

  async archiveMessage(userEmail: string, messageId: string): Promise<boolean> {
    try {
      const gmail = await this.getGmailClient(userEmail);
      
      await gmail.users.messages.modify({
        userId: 'me',
        id: messageId,
        requestBody: {
          removeLabelIds: ['INBOX']
        }
      });
      
      // Clear cache
      this.cache.delete(`message_${userEmail}_${messageId}`);
      this.clearInboxCache(userEmail);
      
      return true;
    } catch (error) {
      console.error('Error archiving message:', error);
      throw error;
    }
  }

  async deleteMessage(userEmail: string, messageId: string): Promise<boolean> {
    try {
      const gmail = await this.getGmailClient(userEmail);
      
      await gmail.users.messages.trash({
        userId: 'me',
        id: messageId
      });
      
      // Clear cache
      this.cache.delete(`message_${userEmail}_${messageId}`);
      this.clearInboxCache(userEmail);
      
      return true;
    } catch (error) {
      console.error('Error deleting message:', error);
      throw error;
    }
  }

  async sendMessage(
    userEmail: string,
    to: string,
    subject: string,
    body: string,
    isHtml: boolean = false
  ): Promise<string> {
    try {
      const gmail = await this.getGmailClient(userEmail);
      
      // Create the email content
      const email = [
        `To: ${to}`,
        `Subject: ${subject}`,
        `Content-Type: ${isHtml ? 'text/html' : 'text/plain'}; charset=utf-8`,
        '',
        body
      ].join('\n');

      // Encode the email in base64
      const encodedEmail = Buffer.from(email)
        .toString('base64')
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=+$/, '');

      const response = await gmail.users.messages.send({
        userId: 'me',
        requestBody: {
          raw: encodedEmail
        }
      });

      // Clear sent messages cache
      this.clearSentCache(userEmail);

      return response.data.id || '';
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  }

  private clearInboxCache(userEmail: string): void {
    // Clear all inbox-related caches for this user
    // This is a simple implementation - in production you might want to be more specific
    const inboxKey = `messages_${userEmail}_in:inbox`;
    for (let i = 1; i <= 100; i++) {
      this.cache.delete(`${inboxKey}_${i}`);
    }
  }

  private clearSentCache(userEmail: string): void {
    const sentKey = `messages_${userEmail}_in:sent`;
    for (let i = 1; i <= 100; i++) {
      this.cache.delete(`${sentKey}_${i}`);
    }
  }

  clearAllCache(): void {
    this.cache.clear();
  }
}

// Export singleton instance
export const gmailService = new GmailService();