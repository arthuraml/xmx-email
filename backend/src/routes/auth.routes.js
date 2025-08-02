const express = require('express');
const router = express.Router();
const googleAuth = require('../config/google.config');

// Initiate OAuth2 authentication flow
router.get('/auth', async (req, res) => {
  try {
    // Check if already authenticated
    const test = await googleAuth.testConnection();
    
    if (test.connected) {
      return res.json({
        success: true,
        message: 'Already authenticated',
        email: test.email
      });
    }

    // Get auth URL
    const authUrl = googleAuth.getAuthUrl();
    
    // Return auth URL for user to visit
    res.json({
      success: true,
      message: 'Visit the URL below to authenticate',
      authUrl: authUrl,
      instructions: 'After authorizing, you will be redirected back to complete the authentication.'
    });

  } catch (error) {
    console.error('Auth route error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Handle OAuth2 callback
router.get('/auth/google/callback', async (req, res) => {
  try {
    const { code } = req.query;
    
    if (!code) {
      throw new Error('No authorization code received');
    }

    // Handle the callback and exchange code for tokens
    await googleAuth.handleCallback(code);
    
    // Send success HTML response
    res.send(`
      <html>
        <head>
          <title>Autenticação Concluída</title>
          <style>
            body {
              font-family: Arial, sans-serif;
              display: flex;
              justify-content: center;
              align-items: center;
              height: 100vh;
              margin: 0;
              background-color: #f5f5f5;
            }
            .container {
              text-align: center;
              padding: 50px;
              background: white;
              border-radius: 10px;
              box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 { color: #4CAF50; }
            p { color: #666; margin: 20px 0; }
            .button {
              display: inline-block;
              padding: 10px 20px;
              background: #4CAF50;
              color: white;
              text-decoration: none;
              border-radius: 5px;
              margin-top: 20px;
            }
          </style>
        </head>
        <body>
          <div class="container">
            <h1>✅ Autenticação Concluída!</h1>
            <p>Sua conta do Gmail foi conectada com sucesso.</p>
            <p>Você já pode fechar esta janela e voltar ao aplicativo.</p>
            <a href="http://localhost:3000" class="button">Ir para o App</a>
          </div>
          <script>
            // Auto close after 5 seconds
            setTimeout(() => {
              window.location.href = 'http://localhost:3000';
            }, 5000);
          </script>
        </body>
      </html>
    `);

  } catch (error) {
    console.error('Callback error:', error);
    res.status(500).send(`
      <html>
        <head>
          <title>Erro de Autenticação</title>
          <style>
            body {
              font-family: Arial, sans-serif;
              display: flex;
              justify-content: center;
              align-items: center;
              height: 100vh;
              margin: 0;
              background-color: #f5f5f5;
            }
            .container {
              text-align: center;
              padding: 50px;
              background: white;
              border-radius: 10px;
              box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 { color: #f44336; }
            p { color: #666; margin: 20px 0; }
            pre {
              background: #f5f5f5;
              padding: 10px;
              border-radius: 5px;
              text-align: left;
              overflow-x: auto;
            }
          </style>
        </head>
        <body>
          <div class="container">
            <h1>❌ Erro de Autenticação</h1>
            <p>Ocorreu um erro durante a autenticação:</p>
            <pre>${error.message}</pre>
            <p>Por favor, tente novamente.</p>
          </div>
        </body>
      </html>
    `);
  }
});

// Check authentication status
router.get('/status', async (req, res) => {
  try {
    const test = await googleAuth.testConnection();
    res.json(test);
  } catch (error) {
    res.status(500).json({
      connected: false,
      error: error.message
    });
  }
});

// Logout (remove saved tokens)
router.post('/logout', async (req, res) => {
  try {
    const fs = require('fs').promises;
    const path = require('path');
    const tokenPath = path.join(__dirname, '../../tokens.json');
    
    await fs.unlink(tokenPath).catch(() => {});
    
    res.json({
      success: true,
      message: 'Logged out successfully'
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

module.exports = router;