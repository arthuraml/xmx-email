import { NextRequest, NextResponse } from 'next/server'

// Fetch processed emails from Python backend
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const limit = searchParams.get('limit') || '100'
    const offset = searchParams.get('offset') || '0'
    
    // Call Python backend API
    const aiBackendUrl = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000'
    const apiKey = process.env.AI_API_KEY || 'your-api-key'
    
    const response = await fetch(
      `${aiBackendUrl}/api/v1/analytics/processed?limit=${limit}&offset=${offset}`,
      {
        method: 'GET',
        headers: {
          'X-API-Key': apiKey
        }
      }
    )
    
    if (!response.ok) {
      console.error('Backend API error:', response.status, response.statusText)
      return NextResponse.json(
        { error: 'Failed to fetch processed emails' },
        { status: 500 }
      )
    }
    
    const data = await response.json()
    
    // Format emails for frontend compatibility
    const formattedEmails = data.emails?.map((email: any) => ({
      email_id: email.email_id,
      from_address: email.from_address,
      to_address: email.to_address,
      subject: email.subject,
      body: email.body,
      received_at: email.received_at,
      
      // Classification
      is_support: email.is_support,
      is_tracking: email.is_tracking,
      classification_type: determineClassificationType(email.is_support, email.is_tracking),
      urgency: email.urgency || 'medium',
      confidence: email.classification_confidence || 0,
      product_name: email.product_name,
      
      // Response (se houver no futuro)
      suggested_subject: email.suggested_subject,
      suggested_body: email.suggested_body,
      response_tone: email.response_tone,
      response_approved: email.response_approved,
      response_sent: email.response_sent,
      response_generated: email.response_generated,
      
      // Tracking (se houver)
      tracking_data: email.tracking_data,
      
      // Costs
      cost_total_brl: email.cost_total_brl || 0,
      cost_total_usd: email.cost_total_usd || 0,
      exchange_rate: email.exchange_rate || 0,
      total_tokens: email.total_tokens || 0,
      
      // Timestamps
      processed_at: email.processed_at || email.created_at
    })) || []
    
    return NextResponse.json({
      success: true,
      emails: formattedEmails,
      pagination: data.pagination,
      summary: data.summary
    })
    
  } catch (error) {
    console.error('Error in processed emails API:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

function determineClassificationType(isSupport: boolean, isTracking: boolean): string {
  if (isSupport && isTracking) return 'both'
  if (isSupport) return 'support'
  if (isTracking) return 'tracking'
  return 'none'
}