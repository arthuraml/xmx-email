import { NextRequest, NextResponse } from 'next/server'

// Fetch processed emails from Python backend via Node.js
export async function GET(request: NextRequest) {
  try {
    // For now, fetch from Supabase directly
    // In production, this would go through the Python backend
    const { createClient } = await import('@/utils/supabase/server')
    const supabase = await createClient()
    
    // Fetch processed emails with their responses and costs
    const { data: processedEmails, error } = await supabase
      .from('processed_emails')
      .select(`
        *,
        llm_responses (
          suggested_subject,
          suggested_body,
          tone,
          approved,
          sent,
          confidence,
          cost_total_brl,
          cost_total_usd
        ),
        tracking_requests (
          order_id,
          tracking_code,
          status,
          tracking_details
        )
      `)
      .order('received_at', { ascending: false })
      .limit(50)
    
    if (error) {
      console.error('Error fetching processed emails:', error)
      return NextResponse.json(
        { error: 'Failed to fetch processed emails' },
        { status: 500 }
      )
    }
    
    // Format emails for frontend
    const formattedEmails = processedEmails?.map(email => ({
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
      
      // Response
      suggested_subject: email.llm_responses?.[0]?.suggested_subject,
      suggested_body: email.llm_responses?.[0]?.suggested_body,
      response_tone: email.llm_responses?.[0]?.tone,
      response_approved: email.llm_responses?.[0]?.approved,
      response_sent: email.llm_responses?.[0]?.sent,
      
      // Tracking
      tracking_data: email.tracking_requests?.[0] ? {
        order_id: email.tracking_requests[0].order_id,
        tracking_code: email.tracking_requests[0].tracking_code,
        status: email.tracking_requests[0].status,
        last_location: email.tracking_requests[0].tracking_details?.last_location || null
      } : undefined,
      
      // Costs
      cost_total_brl: email.cost_total_brl || email.llm_responses?.[0]?.cost_total_brl || 0,
      cost_total_usd: email.cost_total_usd || email.llm_responses?.[0]?.cost_total_usd || 0,
      exchange_rate: email.exchange_rate || 0,
      total_tokens: email.total_tokens || 0,
      
      // Timestamps
      processed_at: email.processed_at
    })) || []
    
    return NextResponse.json({
      success: true,
      emails: formattedEmails
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