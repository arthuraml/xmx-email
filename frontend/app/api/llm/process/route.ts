import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/utils/supabase/server'
import { gmailService } from '@/lib/gmail-service'

// Process email through Python AI backend
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { email_id } = body
    
    if (!email_id) {
      return NextResponse.json(
        { error: 'Email ID is required' },
        { status: 400 }
      )
    }
    
    // Get authenticated user
    const supabase = await createClient()
    const { data: { user }, error: userError } = await supabase.auth.getUser()
    
    if (userError || !user) {
      return NextResponse.json(
        { error: 'User not authenticated' },
        { status: 401 }
      )
    }
    
    // Fetch actual email details from Gmail
    let emailData
    try {
      const emailDetails = await gmailService.getMessageDetails(user.email!, email_id)
      emailData = {
        email_id: emailDetails.id,
        from_address: emailDetails.from,
        to_address: emailDetails.to,
        subject: emailDetails.subject,
        body: emailDetails.body,
        received_at: emailDetails.date.toISOString()
      }
    } catch (gmailError) {
      // Fallback to mock data if Gmail fetch fails
      console.error('Gmail fetch error, using mock data:', gmailError)
      emailData = {
        email_id,
        from_address: 'cliente@example.com',
        to_address: 'support@biofraga.com',
        subject: 'Teste de processamento',
        body: 'Este é um teste de processamento de e-mail',
        received_at: new Date().toISOString()
      }
    }
    
    // Call Python AI backend to process email
    const aiBackendUrl = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000'
    const apiKey = process.env.AI_API_KEY || 'your-api-key'
    
    // Step 1: Process the email (classification + tracking)
    const processingResponse = await fetch(`${aiBackendUrl}/api/v1/emails/process`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey
      },
      body: JSON.stringify(emailData)
    })
    
    if (!processingResponse.ok) {
      const error = await processingResponse.json()
      return NextResponse.json(
        { error: error.detail || 'Failed to process email' },
        { status: processingResponse.status }
      )
    }
    
    const processingResult = await processingResponse.json()
    const classification = processingResult.classification
    const trackingData = processingResult.tracking_data
    
    // Step 2: Tracking data is already included in the processing result
    // No need for separate tracking call anymore
    
    // Step 3: Generate response if needed
    let generatedResponse = null
    let responseError = null
    let responseGenerated = false
    
    // Only generate response if product is identified AND (is_support OR is_tracking)
    if (classification && classification.product_name && (classification.is_support || classification.is_tracking)) {
      const responseGeneration = await fetch(`${aiBackendUrl}/api/v1/response/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey
        },
        body: JSON.stringify({
          email_id: emailData.email_id,
          email_content: emailData,
          classification: classification,
          tracking_data: trackingData
        })
      })
      
      responseGenerated = true
      
      if (responseGeneration.ok) {
        generatedResponse = await responseGeneration.json()
        
        // Check if the response indicates an error
        if (generatedResponse.response_type === 'error' || generatedResponse.error) {
          responseError = generatedResponse.error || 'Erro ao gerar resposta'
        }
      } else {
        try {
          const errorData = await responseGeneration.json()
          responseError = errorData.detail || 'Erro ao gerar resposta'
        } catch {
          responseError = 'Erro ao gerar resposta'
        }
      }
    }
    
    // If there was an error in response generation, return with success: false
    if (responseError) {
      return NextResponse.json({
        success: false,
        email_id: emailData.email_id,
        classification,
        tracking_data: trackingData,
        generated_response: generatedResponse,
        tokens: processingResult.tokens,
        processing_time: processingResult.processing_time,
        error: `E-mail processado mas houve erro na geração da resposta: ${responseError}`
      })
    }
    
    // Add informational message if no product was identified
    let message = null
    if (classification && !classification.product_name) {
      message = 'Email processado mas não foi gerada resposta pois não se refere a nenhum produto conhecido (Alphacur, Arialief, Blinzador, GoldenFrib, Kymezol, Presgera)'
    } else if (!responseGenerated) {
      message = 'Email processado mas não foi gerada resposta pois não é uma solicitação de suporte ou rastreamento'
    }
    
    return NextResponse.json({
      success: true,
      email_id: emailData.email_id,
      classification,
      tracking_data: trackingData,
      generated_response: generatedResponse,
      response_generated: responseGenerated,
      tokens: processingResult.tokens,
      processing_time: processingResult.processing_time,
      message
    })
    
  } catch (error) {
    console.error('Error processing email:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}