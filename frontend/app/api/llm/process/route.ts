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
    const aiBackendUrl = process.env.NEXT_PUBLIC_AI_API_URL || 'http://localhost:8001/api/v1'
    const apiKey = process.env.AI_API_KEY || 'your-api-key'
    
    // Step 1: Classify the email
    const classificationResponse = await fetch(`${aiBackendUrl}/classification/classify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify(emailData)
    })
    
    if (!classificationResponse.ok) {
      const error = await classificationResponse.json()
      return NextResponse.json(
        { error: error.detail || 'Failed to classify email' },
        { status: classificationResponse.status }
      )
    }
    
    const classification = await classificationResponse.json()
    
    // Step 2: Check for tracking data if needed
    let trackingData = null
    if (classification.is_tracking) {
      try {
        const trackingResponse = await fetch(
          `${aiBackendUrl}/tracking/search?email=${encodeURIComponent(emailData.from_address)}`,
          {
            headers: {
              'Authorization': `Bearer ${apiKey}`
            }
          }
        )
        
        if (trackingResponse.ok) {
          const tracking = await trackingResponse.json()
          if (tracking.orders && tracking.orders.length > 0) {
            trackingData = tracking.orders[0]
          }
        }
      } catch (trackingError) {
        console.error('Tracking fetch error:', trackingError)
      }
    }
    
    // Step 3: Generate response if needed
    let generatedResponse = null
    if (classification.is_support || classification.is_tracking) {
      const responseGeneration = await fetch(`${aiBackendUrl}/response/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`
        },
        body: JSON.stringify({
          email_id: emailData.email_id,
          email_content: emailData,
          classification: classification,
          tracking_data: trackingData
        })
      })
      
      if (responseGeneration.ok) {
        generatedResponse = await responseGeneration.json()
      }
    }
    
    return NextResponse.json({
      success: true,
      email_id: emailData.email_id,
      classification,
      tracking_data: trackingData,
      generated_response: generatedResponse
    })
    
  } catch (error) {
    console.error('Error processing email:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}