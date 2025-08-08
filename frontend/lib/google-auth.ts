import { google } from 'googleapis';
import { OAuth2Client } from 'google-auth-library';
import { createClient } from '@/utils/supabase/server';

export interface OAuthTokens {
  access_token: string;
  refresh_token?: string;
  expiry_date?: number;
  scope?: string;
  token_type?: string;
}

export interface GmailProfile {
  emailAddress: string;
  messagesTotal?: number;
  threadsTotal?: number;
  historyId?: string;
}

export class GoogleAuthService {
  private oAuth2Client: OAuth2Client;
  private readonly SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.labels'
  ];

  constructor() {
    const clientId = process.env.GOOGLE_CLIENT_ID;
    const clientSecret = process.env.GOOGLE_CLIENT_SECRET;
    const redirectUri = process.env.NODE_ENV === 'production'
      ? process.env.GOOGLE_REDIRECT_URI_PROD
      : process.env.GOOGLE_REDIRECT_URI;

    // Validate required environment variables
    if (!clientId || !clientSecret || !redirectUri) {
      const missing = [];
      if (!clientId) missing.push('GOOGLE_CLIENT_ID');
      if (!clientSecret) missing.push('GOOGLE_CLIENT_SECRET');
      if (!redirectUri) missing.push(process.env.NODE_ENV === 'production' ? 'GOOGLE_REDIRECT_URI_PROD' : 'GOOGLE_REDIRECT_URI');
      
      throw new Error(`Missing required environment variables: ${missing.join(', ')}. Please check your .env file.`);
    }

    this.oAuth2Client = new google.auth.OAuth2(
      clientId,
      clientSecret,
      redirectUri
    );
  }

  /**
   * Generate OAuth2 authorization URL
   */
  getAuthUrl(): string {
    return this.oAuth2Client.generateAuthUrl({
      access_type: 'offline',
      scope: this.SCOPES,
      prompt: 'select_account consent', // Show account selection and force consent to get refresh token
      state: this.generateStateToken() // CSRF protection
    });
  }

  /**
   * Generate a random state token for CSRF protection
   */
  private generateStateToken(): string {
    return Math.random().toString(36).substring(2, 15) + 
           Math.random().toString(36).substring(2, 15);
  }

  /**
   * Exchange authorization code for tokens
   */
  async handleCallback(code: string): Promise<OAuthTokens> {
    try {
      const { tokens } = await this.oAuth2Client.getToken(code);
      return tokens as OAuthTokens;
    } catch (error) {
      console.error('Error exchanging code for tokens:', error);
      throw new Error('Failed to exchange authorization code');
    }
  }

  /**
   * Save tokens to Supabase
   */
  async saveTokens(userEmail: string, tokens: OAuthTokens, gmailProfile?: GmailProfile) {
    const supabase = await createClient();
    
    const { error } = await supabase
      .from('oauth_tokens')
      .upsert({
        user_email: userEmail,
        access_token: tokens.access_token,
        refresh_token: tokens.refresh_token,
        expiry_date: tokens.expiry_date,
        scope: tokens.scope,
        token_type: tokens.token_type || 'Bearer',
        gmail_profile: gmailProfile,
        last_used: new Date().toISOString()
      }, {
        onConflict: 'user_email'
      });

    if (error) {
      console.error('Error saving tokens to Supabase:', error);
      throw new Error('Failed to save authentication tokens');
    }
  }

  /**
   * Load tokens from Supabase
   */
  async loadTokens(userEmail: string): Promise<OAuthTokens | null> {
    const supabase = await createClient();
    
    const { data, error } = await supabase
      .from('oauth_tokens')
      .select('*')
      .eq('user_email', userEmail)
      .single();

    if (error || !data) {
      return null;
    }

    // Check if token is expired and refresh if needed
    if (data.expiry_date && data.expiry_date < Date.now()) {
      if (data.refresh_token) {
        try {
          const refreshedTokens = await this.refreshAccessToken(data.refresh_token);
          await this.saveTokens(userEmail, refreshedTokens);
          return refreshedTokens;
        } catch (error) {
          console.error('Failed to refresh token:', error);
          return null;
        }
      }
    }

    return {
      access_token: data.access_token,
      refresh_token: data.refresh_token,
      expiry_date: data.expiry_date,
      scope: data.scope,
      token_type: data.token_type
    };
  }

  /**
   * Refresh access token using refresh token
   */
  async refreshAccessToken(refreshToken: string): Promise<OAuthTokens> {
    this.oAuth2Client.setCredentials({ refresh_token: refreshToken });
    
    try {
      const { credentials } = await this.oAuth2Client.refreshAccessToken();
      return credentials as OAuthTokens;
    } catch (error) {
      console.error('Error refreshing access token:', error);
      throw new Error('Failed to refresh access token');
    }
  }

  /**
   * Get authenticated OAuth2 client
   */
  async getAuthenticatedClient(userEmail: string): Promise<OAuth2Client | null> {
    const tokens = await this.loadTokens(userEmail);
    
    if (!tokens) {
      return null;
    }

    this.oAuth2Client.setCredentials(tokens);
    
    // Update last_used timestamp
    const supabase = await createClient();
    await supabase
      .from('oauth_tokens')
      .update({ last_used: new Date().toISOString() })
      .eq('user_email', userEmail);

    return this.oAuth2Client;
  }

  /**
   * Test Gmail connection
   */
  async testConnection(userEmail: string): Promise<{ connected: boolean; profile?: GmailProfile; error?: string }> {
    try {
      const authClient = await this.getAuthenticatedClient(userEmail);
      
      if (!authClient) {
        return { 
          connected: false, 
          error: 'No authentication tokens found' 
        };
      }

      const gmail = google.gmail({ version: 'v1', auth: authClient });
      const profile = await gmail.users.getProfile({ userId: 'me' });
      
      const gmailProfile: GmailProfile = {
        emailAddress: profile.data.emailAddress!,
        messagesTotal: profile.data.messagesTotal,
        threadsTotal: profile.data.threadsTotal,
        historyId: profile.data.historyId
      };

      // Update profile in database
      await this.updateGmailProfile(userEmail, gmailProfile);

      return { 
        connected: true, 
        profile: gmailProfile 
      };
    } catch (error: any) {
      console.error('Gmail connection test failed:', error);
      
      if (error.code === 401) {
        return { 
          connected: false, 
          error: 'Authentication expired. Please re-authenticate.' 
        };
      }
      
      return { 
        connected: false, 
        error: error.message || 'Connection test failed' 
      };
    }
  }

  /**
   * Update Gmail profile in database
   */
  private async updateGmailProfile(userEmail: string, profile: GmailProfile) {
    const supabase = await createClient();
    
    await supabase
      .from('oauth_tokens')
      .update({ 
        gmail_profile: profile,
        updated_at: new Date().toISOString()
      })
      .eq('user_email', userEmail);
  }

  /**
   * Remove authentication tokens (logout)
   */
  async removeTokens(userEmail: string): Promise<void> {
    const supabase = await createClient();
    
    const { error } = await supabase
      .from('oauth_tokens')
      .delete()
      .eq('user_email', userEmail);

    if (error) {
      console.error('Error removing tokens:', error);
      throw new Error('Failed to remove authentication tokens');
    }
  }

  /**
   * Get Gmail API client
   */
  async getGmailClient(userEmail: string) {
    const authClient = await this.getAuthenticatedClient(userEmail);
    
    if (!authClient) {
      throw new Error('Not authenticated. Please login first.');
    }

    return google.gmail({ version: 'v1', auth: authClient });
  }
}

// Export singleton instance
export const googleAuth = new GoogleAuthService();