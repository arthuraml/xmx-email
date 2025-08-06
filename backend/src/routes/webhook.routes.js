const express = require('express');
const router = express.Router();
const axios = require('axios');

// Python backend URL
const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || 'http://localhost:8001';
const PYTHON_API_KEY = process.env.API_KEY || 'cefc0ee900bc2234c94e0df6566aa4fe1e1703cc42d64b858347cfa83e03b774';

/**
 * Webhook para processar e-mails em tempo real
 * Este endpoint recebe um e-mail e executa o fluxo completo:
 * 1. Classifica o e-mail (suporte/rastreamento)
 * 2. Busca dados de rastreamento se necessário
 * 3. Gera resposta apropriada
 */
router.post('/process-email', async (req, res) => {
  try {
    const { 
      email_id, 
      from, 
      to, 
      subject, 
      body, 
      received_at,
      thread_id 
    } = req.body;

    console.log(`Processing email ${email_id} from ${from}`);

    // Validação básica
    if (!email_id || !from || !to || !subject || !body) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields'
      });
    }

    // Headers para autenticação com backend Python
    const headers = {
      'Content-Type': 'application/json',
      'X-API-Key': PYTHON_API_KEY
    };

    // STEP 1: Classificar e-mail
    console.log('Step 1: Classifying email...');
    const classificationResponse = await axios.post(
      `${PYTHON_BACKEND_URL}/api/v1/classification/classify`,
      {
        email_id,
        from_address: from,
        to_address: to,
        subject,
        body,
        received_at: received_at || new Date().toISOString(),
        thread_id
      },
      { headers }
    );

    const classification = classificationResponse.data;
    console.log(`Classification: Support=${classification.is_support}, Tracking=${classification.is_tracking}`);

    // STEP 2: Buscar dados de rastreamento se necessário
    let trackingData = null;
    if (classification.is_tracking) {
      console.log('Step 2: Querying tracking data...');
      
      try {
        const trackingResponse = await axios.post(
          `${PYTHON_BACKEND_URL}/api/v1/tracking/query`,
          {
            email_id,
            sender_email: classification.sender_email || from
          },
          { headers }
        );

        if (trackingResponse.data.found) {
          trackingData = trackingResponse.data.tracking_data;
          console.log(`Tracking found: ${trackingData.order_id} - ${trackingData.status}`);
        } else {
          console.log('No tracking data found');
        }
      } catch (trackingError) {
        console.error('Error querying tracking:', trackingError.message);
        // Continue without tracking data
      }
    } else {
      console.log('Step 2: Skipped (not a tracking request)');
    }

    // STEP 3: Gerar resposta
    console.log('Step 3: Generating response...');
    const responseGenerationPayload = {
      email_id,
      email_content: {
        from,
        to,
        subject,
        body,
        received_at: received_at || new Date().toISOString()
      },
      classification: {
        is_support: classification.is_support,
        is_tracking: classification.is_tracking,
        urgency: classification.urgency,
        email_type: classification.email_type
      }
    };

    // Adiciona dados de rastreamento se disponível
    if (trackingData) {
      responseGenerationPayload.tracking_data = trackingData;
    }

    const responseResponse = await axios.post(
      `${PYTHON_BACKEND_URL}/api/v1/response/generate`,
      responseGenerationPayload,
      { headers }
    );

    const generatedResponse = responseResponse.data;
    console.log(`Response generated: ${generatedResponse.response_type}`);

    // Retorna resultado completo
    res.json({
      success: true,
      email_id,
      classification: {
        is_support: classification.is_support,
        is_tracking: classification.is_tracking,
        type: classification.classification_type,
        confidence: classification.confidence
      },
      tracking: trackingData ? {
        found: true,
        order_id: trackingData.order_id,
        status: trackingData.status,
        tracking_code: trackingData.tracking_code
      } : {
        found: false
      },
      response: {
        subject: generatedResponse.suggested_subject,
        body: generatedResponse.suggested_body,
        tone: generatedResponse.tone,
        requires_followup: generatedResponse.requires_followup
      },
      processing: {
        total_time_ms: (
          (classification.processing_time_ms || 0) + 
          (trackingData ? 50 : 0) + 
          (generatedResponse.processing_time_ms || 0)
        ),
        tokens_used: generatedResponse.total_tokens || 0
      }
    });

  } catch (error) {
    console.error('Webhook processing error:', error);
    
    // Retorna erro estruturado
    res.status(500).json({
      success: false,
      error: error.message,
      details: error.response?.data || null
    });
  }
});

/**
 * Webhook para processar múltiplos e-mails em lote
 */
router.post('/process-batch', async (req, res) => {
  try {
    const { emails } = req.body;

    if (!emails || !Array.isArray(emails) || emails.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Invalid or empty emails array'
      });
    }

    console.log(`Processing batch of ${emails.length} emails`);

    const results = [];
    const errors = [];

    // Processa cada e-mail
    for (const email of emails) {
      try {
        const response = await axios.post(
          'http://localhost:3001/api/webhook/process-email',
          email
        );
        results.push(response.data);
      } catch (error) {
        errors.push({
          email_id: email.email_id,
          error: error.message
        });
      }
    }

    res.json({
      success: true,
      total: emails.length,
      processed: results.length,
      failed: errors.length,
      results,
      errors
    });

  } catch (error) {
    console.error('Batch processing error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * Webhook de teste para verificar conectividade
 */
router.get('/test', async (req, res) => {
  try {
    // Testa conexão com backend Python
    const headers = {
      'X-API-Key': PYTHON_API_KEY
    };

    const healthCheck = await axios.get(
      `${PYTHON_BACKEND_URL}/api/v1/health`,
      { headers }
    );

    res.json({
      success: true,
      message: 'Webhook service is working',
      python_backend: {
        url: PYTHON_BACKEND_URL,
        status: healthCheck.data.status || 'connected'
      }
    });

  } catch (error) {
    res.json({
      success: false,
      message: 'Webhook service error',
      python_backend: {
        url: PYTHON_BACKEND_URL,
        status: 'disconnected',
        error: error.message
      }
    });
  }
});

/**
 * Endpoint para receber notificações do Gmail (futuro)
 * Quando um novo e-mail chegar, o Gmail pode chamar este webhook
 */
router.post('/gmail-notification', async (req, res) => {
  try {
    const { message } = req.body;
    
    // Decodifica a mensagem do Gmail
    const messageData = JSON.parse(
      Buffer.from(message.data, 'base64').toString()
    );

    console.log('Gmail notification received:', messageData);

    // TODO: Buscar detalhes do e-mail usando Gmail API
    // TODO: Processar e-mail usando o webhook process-email

    res.status(200).send();

  } catch (error) {
    console.error('Gmail notification error:', error);
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;