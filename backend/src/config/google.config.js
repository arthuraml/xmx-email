// This file now uses OAuth2 instead of Service Account
// due to organization policy restrictions

const googleOAuth = require('./google-oauth.config');

// Initialize on module load
googleOAuth.initialize().catch(console.error);

module.exports = googleOAuth;