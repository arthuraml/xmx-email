const googleAuth = require('../config/google.config');
const NodeCache = require('node-cache');

class GmailService {
  constructor() {
    // Cache for 5 minutes
    this.cache = new NodeCache({ stdTTL: 300 });
  }

  getGmailClient() {
    return googleAuth.getGmail();
  }

  async listMessages(query, maxResults = 20) {
    const cacheKey = `messages_${query}_${maxResults}`;
    const cached = this.cache.get(cacheKey);
    
    if (cached) {
      return cached;
    }

    try {
      // Get message IDs
      const response = await this.getGmailClient().users.messages.list({
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
            const details = await this.getMessageDetails(message.id);
            return details;
          } catch (error) {
            console.error(`Error fetching message ${message.id}:`, error);
            return null;
          }
        })
      );

      const validMessages = messages.filter(msg => msg !== null);
      this.cache.set(cacheKey, validMessages);
      
      return validMessages;
    } catch (error) {
      console.error('Error listing messages:', error);
      throw error;
    }
  }

  async getMessageDetails(messageId) {
    const cacheKey = `message_${messageId}`;
    const cached = this.cache.get(cacheKey);
    
    if (cached) {
      return cached;
    }

    try {
      const response = await this.getGmailClient().users.messages.get({
        userId: 'me',
        id: messageId
      });

      const message = response.data;
      const headers = message.payload.headers;
      
      // Extract relevant headers
      const from = this.getHeader(headers, 'From');
      const to = this.getHeader(headers, 'To');
      const subject = this.getHeader(headers, 'Subject');
      const date = this.getHeader(headers, 'Date');
      
      // Extract body
      const body = this.extractBody(message.payload);
      
      const formattedMessage = {
        id: message.id,
        threadId: message.threadId,
        from,
        to,
        subject,
        date: new Date(date),
        snippet: message.snippet,
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

  getHeader(headers, name) {
    const header = headers.find(h => h.name.toLowerCase() === name.toLowerCase());
    return header ? header.value : '';
  }

  extractBody(payload) {
    let textBody = '';
    let htmlBody = '';

    const extractFromParts = (parts) => {
      if (!parts) return;

      for (const part of parts) {
        if (part.mimeType === 'text/plain' && part.body.data) {
          textBody = Buffer.from(part.body.data, 'base64').toString('utf-8');
        } else if (part.mimeType === 'text/html' && part.body.data) {
          htmlBody = Buffer.from(part.body.data, 'base64').toString('utf-8');
        } else if (part.parts) {
          extractFromParts(part.parts);
        }
      }
    };

    // Check if body is directly in payload
    if (payload.body && payload.body.data) {
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

  async getInboxMessages(maxResults = 20) {
    return this.listMessages('in:inbox', maxResults);
  }

  async getSentMessages(maxResults = 20) {
    return this.listMessages('in:sent', maxResults);
  }

  async markAsRead(messageId) {
    try {
      await this.getGmailClient().users.messages.modify({
        userId: 'me',
        id: messageId,
        requestBody: {
          removeLabelIds: ['UNREAD']
        }
      });
      
      // Clear cache for this message
      this.cache.del(`message_${messageId}`);
      
      return true;
    } catch (error) {
      console.error('Error marking message as read:', error);
      throw error;
    }
  }

  clearCache() {
    this.cache.flushAll();
  }
}

module.exports = new GmailService();