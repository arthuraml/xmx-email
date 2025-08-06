import { NextRequest, NextResponse } from 'next/server'

// Process email through Python backend
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
    
    // Call Node.js webhook to process email
    const webhookUrl = `${process.env.BACKEND_URL || 'http://localhost:3001'}/api/webhook/process-email`
    
    // First, fetch email details from Gmail or database
    // For now, we'll use mock data
    const emailData = {
      email_id,
      from: 'cliente@example.com',
      to: 'support@biofraga.com',
      subject: 'Teste de processamento',
      body: 'Este é um teste de processamento de e-mail',
      received_at: new Date().toISOString()
    }
    
    const response = await fetch(webhookUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(emailData)
    })
    
    if (!response.ok) {
      const error = await response.json()
      return NextResponse.json(
        { error: error.error || 'Failed to process email' },
        { status: response.status }
      )
    }
    
    const result = await response.json()
    
    return NextResponse.json({
      success: true,
      ...result
    })
    
  } catch (error) {
    console.error('Error processing email:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}