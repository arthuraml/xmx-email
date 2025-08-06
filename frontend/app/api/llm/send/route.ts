import { NextRequest, NextResponse } from 'next/server'

// Send the approved response
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
    
    const { createClient } = await import('@/utils/supabase/server')
    const supabase = await createClient()
    
    // Fetch the response details
    const { data: response, error: fetchError } = await supabase
      .from('llm_responses')
      .select('*')
      .eq('email_id', email_id)
      .single()
    
    if (fetchError || !response) {
      return NextResponse.json(
        { error: 'Response not found' },
        { status: 404 }
      )
    }
    
    // TODO: Here you would integrate with Gmail API to actually send the email
    // For now, we'll just mark it as sent in the database
    
    // Mock sending email via Gmail API
    console.log('Sending email response:', {
      to: 'recipient@example.com',
      subject: response.suggested_subject,
      body: response.suggested_body
    })
    
    // Update the response as sent
    const { error: updateError } = await supabase
      .from('llm_responses')
      .update({
        sent: true,
        sent_at: new Date().toISOString(),
        approved: true // Auto-approve when sending
      })
      .eq('email_id', email_id)
    
    if (updateError) {
      console.error('Error marking response as sent:', updateError)
      return NextResponse.json(
        { error: 'Failed to mark response as sent' },
        { status: 500 }
      )
    }
    
    return NextResponse.json({
      success: true,
      message: 'Response sent successfully'
    })
    
  } catch (error) {
    console.error('Error in send API:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}