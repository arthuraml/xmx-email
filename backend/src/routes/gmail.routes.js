const express = require('express');
const router = express.Router();
const gmailService = require('../services/gmail.service');

// Test connection endpoint
router.get('/test', async (req, res, next) => {
  try {
    const googleAuth = require('../config/google.config');
    const isConnected = await googleAuth.testConnection();
    
    res.json({
      connected: isConnected,
      message: isConnected ? 'Gmail API connection successful' : 'Gmail API connection failed'
    });
  } catch (error) {
    next(error);
  }
});

// Middleware to ensure authentication
const ensureAuth = async (req, res, next) => {
  try {
    const googleAuth = require('../config/google.config');
    await googleAuth.ensureAuthenticated();
    next();
  } catch (error) {
    res.status(401).json({
      success: false,
      error: error.message,
      needsAuth: true,
      authUrl: '/api/gmail/auth'
    });
  }
};

// Get inbox messages
router.get('/inbox', ensureAuth, async (req, res, next) => {
  try {
    const maxResults = parseInt(req.query.limit) || 20;
    const messages = await gmailService.getInboxMessages(maxResults);
    
    res.json({
      success: true,
      count: messages.length,
      messages
    });
  } catch (error) {
    console.error('Inbox route error:', error);
    next(error);
  }
});

// Get sent messages
router.get('/sent', ensureAuth, async (req, res, next) => {
  try {
    const maxResults = parseInt(req.query.limit) || 20;
    const messages = await gmailService.getSentMessages(maxResults);
    
    res.json({
      success: true,
      count: messages.length,
      messages
    });
  } catch (error) {
    console.error('Sent route error:', error);
    next(error);
  }
});

// Get single message details
router.get('/message/:id', ensureAuth, async (req, res, next) => {
  try {
    const { id } = req.params;
    const message = await gmailService.getMessageDetails(id);
    
    res.json({
      success: true,
      message
    });
  } catch (error) {
    console.error('Message detail error:', error);
    next(error);
  }
});

// Mark message as read
router.post('/message/:id/read', ensureAuth, async (req, res, next) => {
  try {
    const { id } = req.params;
    await gmailService.markAsRead(id);
    
    res.json({
      success: true,
      message: 'Message marked as read'
    });
  } catch (error) {
    console.error('Mark as read error:', error);
    next(error);
  }
});

// Search messages
router.get('/search', ensureAuth, async (req, res, next) => {
  try {
    const { q, limit } = req.query;
    
    if (!q) {
      return res.status(400).json({
        success: false,
        error: 'Search query is required'
      });
    }
    
    const maxResults = parseInt(limit) || 20;
    const messages = await gmailService.listMessages(q, maxResults);
    
    res.json({
      success: true,
      count: messages.length,
      query: q,
      messages
    });
  } catch (error) {
    console.error('Search error:', error);
    next(error);
  }
});

// Clear cache endpoint (useful for development)
router.post('/cache/clear', async (req, res, next) => {
  try {
    gmailService.clearCache();
    
    res.json({
      success: true,
      message: 'Cache cleared successfully'
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;