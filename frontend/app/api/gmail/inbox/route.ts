import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/utils/supabase/server';
import { gmailService } from '@/lib/gmail-service';

export async function GET(request: NextRequest) {
  try {
    // Get authenticated user
    const supabase = await createClient();
    const { data: { user }, error: userError } = await supabase.auth.getUser();
    
    if (userError || !user) {
      return NextResponse.json({
        success: false,
        error: 'User not authenticated'
      }, { status: 401 });
    }

    // Get query parameters
    const searchParams = request.nextUrl.searchParams;
    const limit = parseInt(searchParams.get('limit') || '20', 10);
    
    // Fetch inbox messages using the Gmail service
    const messages = await gmailService.getInboxMessages(user.email!, limit);
    
    return NextResponse.json({
      success: true,
      messages,
      count: messages.length
    });
  } catch (error: any) {
    console.error('Error fetching inbox:', error);
    
    // Check if it's an authentication error
    if (error.message?.includes('Not authenticated') || error.message?.includes('authentication')) {
      return NextResponse.json(
        { 
          success: false, 
          error: 'Gmail not connected. Please authenticate first.',
          requiresAuth: true
        },
        { status: 401 }
      );
    }
    
    return NextResponse.json(
      { 
        success: false, 
        error: error.message || 'Failed to fetch inbox messages' 
      },
      { status: 500 }
    );
  }
}