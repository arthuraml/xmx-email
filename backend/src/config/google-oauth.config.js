const { google } = require('googleapis');
const fs = require('fs').promises;
const path = require('path');
const open = require('open');

class GoogleOAuthConfig {
  constructor() {
    this.oAuth2Client = null;
    this.gmail = null;
    this.TOKEN_PATH = path.join(__dirname, '../../tokens.json');
    this.SCOPES = [
      'https://www.googleapis.com/auth/gmail.readonly',
      'https://www.googleapis.com/auth/gmail.modify',
      'https://www.googleapis.com/auth/gmail.labels'
    ];
  }

  async initialize() {
    try {
      // Create OAuth2 client
      this.oAuth2Client = new google.auth.OAuth2(
        process.env.GOOGLE_CLIENT_ID,
        process.env.GOOGLE_CLIENT_SECRET,
        process.env.GOOGLE_REDIRECT_URI
      );

      // Try to load saved tokens
      const tokens = await this.loadSavedTokens();
      
      if (tokens) {
        this.oAuth2Client.setCredentials(tokens);
        console.log('Loaded saved authentication tokens');
      } else {
        console.log('No saved tokens found. Run /api/gmail/auth to authenticate.');
      }

      // Initialize Gmail API
      this.gmail = google.gmail({ version: 'v1', auth: this.oAuth2Client });
      
    } catch (error) {
      console.error('Failed to initialize Google OAuth:', error);
      throw error;
    }
  }

  async loadSavedTokens() {
    try {
      const content = await fs.readFile(this.TOKEN_PATH, 'utf8');
      const tokens = JSON.parse(content);
      
      // Check if token is expired
      if (tokens.expiry_date && tokens.expiry_date < Date.now()) {
        if (tokens.refresh_token) {
          console.log('Access token expired, refreshing...');
          const { credentials } = await this.oAuth2Client.refreshAccessToken();
          await this.saveTokens(credentials);
          return credentials;
        }
      }
      
      return tokens;
    } catch (error) {
      return null;
    }
  }

  async saveTokens(tokens) {
    await fs.writeFile(this.TOKEN_PATH, JSON.stringify(tokens, null, 2));
    console.log('Tokens saved to', this.TOKEN_PATH);
  }

  getAuthUrl() {
    // Generate auth URL
    const authUrl = this.oAuth2Client.generateAuthUrl({
      access_type: 'offline',
      scope: this.SCOPES,
      prompt: 'consent' // Force consent to get refresh token
    });
    
    return authUrl;
  }

  async handleCallback(code) {
    try {
      // Exchange code for tokens
      const { tokens } = await this.oAuth2Client.getToken(code);
      this.oAuth2Client.setCredentials(tokens);
      await this.saveTokens(tokens);
      
      return tokens;
    } catch (error) {
      console.error('Error handling OAuth callback:', error);
      throw error;
    }
  }

  async testConnection() {
    try {
      const profile = await this.gmail.users.getProfile({ userId: 'me' });
      console.log('Gmail connection successful:', profile.data.emailAddress);
      return {
        connected: true,
        email: profile.data.emailAddress
      };
    } catch (error) {
      if (error.code === 401) {
        console.log('Authentication required. Run /api/gmail/auth to authenticate.');
        return {
          connected: false,
          needsAuth: true,
          error: 'Authentication required'
        };
      }
      console.error('Gmail connection test failed:', error);
      return {
        connected: false,
        error: error.message
      };
    }
  }

  async ensureAuthenticated() {
    const test = await this.testConnection();
    if (!test.connected && test.needsAuth) {
      throw new Error('Authentication required. Please visit /api/gmail/auth');
    }
    return test;
  }

  getAuth() {
    return this.oAuth2Client;
  }

  getGmail() {
    return this.gmail;
  }
}

// Create singleton instance
const googleOAuth = new GoogleOAuthConfig();

module.exports = googleOAuth;