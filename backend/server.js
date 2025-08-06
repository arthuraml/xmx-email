require('dotenv').config({ path: '../.env' });
const express = require('express');
const cors = require('cors');
const rateLimit = require('express-rate-limit');

const app = express();
const PORT = process.env.BACKEND_PORT || 3001;

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
});

// Middleware
app.use(cors({
  origin: process.env.NODE_ENV === 'production' 
    ? 'https://yourdomain.com' 
    : 'http://localhost:3000',
  credentials: true
}));
app.use(express.json());
app.use('/api/', limiter);

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Auth routes
const authRoutes = require('./src/routes/auth.routes');
app.use('/api/gmail', authRoutes);

// OAuth callback route (needs to be at root level)
const googleAuth = require('./src/config/google.config');
app.get('/auth/google/callback', async (req, res) => {
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
            // Auto redirect after 3 seconds
            setTimeout(() => {
              window.location.href = 'http://localhost:3000';
            }, 3000);
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

// Gmail routes
const gmailRoutes = require('./src/routes/gmail.routes');
app.use('/api/gmail', gmailRoutes);

// Webhook routes for email processing
const webhookRoutes = require('./src/routes/webhook.routes');
app.use('/api/webhook', webhookRoutes);

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(err.status || 500).json({
    error: {
      message: err.message || 'Internal server error',
      status: err.status || 500
    }
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

app.listen(PORT, () => {
  console.log(`Backend server running on http://localhost:${PORT}`);
  console.log(`Health check available at http://localhost:${PORT}/health`);
});