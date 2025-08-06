import { NextRequest, NextResponse } from 'next/server'

// Approve a suggested response
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { email_id, body: updatedBody } = body
    
    if (!email_id) {
      return NextResponse.json(
        { error: 'Email ID is required' },
        { status: 400 }
      )
    }
    
    const { createClient } = await import('@/utils/supabase/server')
    const supabase = await createClient()
    
    // Update the response as approved
    const updateData: any = {
      approved: true,
      updated_at: new Date().toISOString()
    }
    
    // If body was edited, update it
    if (updatedBody) {
      updateData.suggested_body = updatedBody
    }
    
    const { error } = await supabase
      .from('llm_responses')
      .update(updateData)
      .eq('email_id', email_id)
    
    if (error) {
      console.error('Error approving response:', error)
      return NextResponse.json(
        { error: 'Failed to approve response' },
        { status: 500 }
      )
    }
    
    return NextResponse.json({
      success: true,
      message: 'Response approved successfully'
    })
    
  } catch (error) {
    console.error('Error in approve API:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}