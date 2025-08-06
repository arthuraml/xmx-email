import { NextRequest, NextResponse } from 'next/server';

// Python backend configuration
const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || 'http://localhost:8001';
const PYTHON_API_KEY = process.env.API_KEY || 'cefc0ee900bc2234c94e0df6566aa4fe1e1703cc42d64b858347cfa83e03b774';

interface EmailProcessingRequest {
  email_id: string;
  from: string;
  to: string;
  subject: string;
  body: string;
  received_at?: string;
  thread_id?: string;
}

interface ClassificationResponse {
  is_support: boolean;
  is_tracking: boolean;
  sender_email?: string;
  urgency?: string;
  email_type?: string;
  classification_type?: string;
  confidence?: number;
  processing_time_ms?: number;
}

interface TrackingData {
  order_id: string;
  customer_email: string;
  tracking_code: string;
  status: string;
  carrier?: string;
  shipped_date?: string;
  expected_delivery?: string;
  last_update?: string;
  origin?: string;
  destination?: string;
  items?: any[];
}

interface ResponseGenerationResponse {
  suggested_subject: string;
  suggested_body: string;
  response_type: string;
  tone?: string;
  requires_followup?: boolean;
  processing_time_ms?: number;
  total_tokens?: number;
}

/**
 * Webhook para processar e-mails em tempo real
 * Este endpoint recebe um e-mail e executa o fluxo completo:
 * 1. Classifica o e-mail (suporte/rastreamento)
 * 2. Busca dados de rastreamento se necessário
 * 3. Gera resposta apropriada
 */
export async function POST(request: NextRequest) {
  try {
    const body: EmailProcessingRequest = await request.json();
    const { 
      email_id, 
      from, 
      to, 
      subject, 
      body: emailBody, 
      received_at,
      thread_id 
    } = body;

    console.log(`Processing email ${email_id} from ${from}`);

    // Validação básica
    if (!email_id || !from || !to || !subject || !emailBody) {
      return NextResponse.json({
        success: false,
        error: 'Missing required fields'
      }, { status: 400 });
    }

    // Headers para autenticação com backend Python
    const headers = {
      'Content-Type': 'application/json',
      'X-API-Key': PYTHON_API_KEY
    };

    // STEP 1: Classificar e-mail
    console.log('Step 1: Classifying email...');
    const classificationResponse = await fetch(
      `${PYTHON_BACKEND_URL}/api/v1/classification/classify`,
      {
        method: 'POST',
        headers,
        body: JSON.stringify({
          email_id,
          from_address: from,
          to_address: to,
          subject,
          body: emailBody,
          received_at: received_at || new Date().toISOString(),
          thread_id
        })
      }
    );

    if (!classificationResponse.ok) {
      throw new Error(`Classification failed: ${classificationResponse.statusText}`);
    }

    const classification: ClassificationResponse = await classificationResponse.json();
    console.log(`Classification: Support=${classification.is_support}, Tracking=${classification.is_tracking}`);

    // STEP 2: Buscar dados de rastreamento se necessário
    let trackingData: TrackingData | null = null;
    if (classification.is_tracking) {
      console.log('Step 2: Querying tracking data...');
      
      try {
        const trackingResponse = await fetch(
          `${PYTHON_BACKEND_URL}/api/v1/tracking/query`,
          {
            method: 'POST',
            headers,
            body: JSON.stringify({
              email_id,
              sender_email: classification.sender_email || from
            })
          }
        );

        if (trackingResponse.ok) {
          const trackingResult = await trackingResponse.json();
          if (trackingResult.found) {
            trackingData = trackingResult.tracking_data;
            console.log(`Tracking found: ${trackingData.order_id} - ${trackingData.status}`);
          } else {
            console.log('No tracking data found');
          }
        }
      } catch (trackingError: any) {
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
        body: emailBody,
        received_at: received_at || new Date().toISOString()
      },
      classification: {
        is_support: classification.is_support,
        is_tracking: classification.is_tracking,
        urgency: classification.urgency,
        email_type: classification.email_type
      },
      ...(trackingData && { tracking_data: trackingData })
    };

    const responseResponse = await fetch(
      `${PYTHON_BACKEND_URL}/api/v1/response/generate`,
      {
        method: 'POST',
        headers,
        body: JSON.stringify(responseGenerationPayload)
      }
    );

    if (!responseResponse.ok) {
      throw new Error(`Response generation failed: ${responseResponse.statusText}`);
    }

    const generatedResponse: ResponseGenerationResponse = await responseResponse.json();
    console.log(`Response generated: ${generatedResponse.response_type}`);

    // Retorna resultado completo
    return NextResponse.json({
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

  } catch (error: any) {
    console.error('Webhook processing error:', error);
    
    // Retorna erro estruturado
    return NextResponse.json({
      success: false,
      error: error.message,
      details: error.response?.data || null
    }, { status: 500 });
  }
}