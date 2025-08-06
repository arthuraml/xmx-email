import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/utils/supabase/server';
import { gmailService } from '@/lib/gmail-service';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
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

    // Fetch message details using the Gmail service
    const message = await gmailService.getMessageDetails(user.email!, params.id);
    
    return NextResponse.json({
      success: true,
      message
    });
  } catch (error: any) {
    console.error('Error fetching message:', error);
    
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
        error: error.message || 'Failed to fetch message' 
      },
      { status: 500 }
    );
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
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

    const url = request.nextUrl.pathname;
    
    // Handle mark as read
    if (url.endsWith('/read')) {
      const success = await gmailService.markAsRead(user.email!, params.id);
      return NextResponse.json({ success });
    }
    
    // Handle mark as unread
    if (url.endsWith('/unread')) {
      const success = await gmailService.markAsUnread(user.email!, params.id);
      return NextResponse.json({ success });
    }
    
    // Handle archive
    if (url.endsWith('/archive')) {
      const success = await gmailService.archiveMessage(user.email!, params.id);
      return NextResponse.json({ success });
    }
    
    // Handle delete (move to trash)
    if (url.endsWith('/delete')) {
      const success = await gmailService.deleteMessage(user.email!, params.id);
      return NextResponse.json({ success });
    }

    return NextResponse.json(
      { success: false, error: 'Invalid endpoint' },
      { status: 404 }
    );
  } catch (error: any) {
    console.error('Error in POST request:', error);
    
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
        error: error.message || 'Failed to process request' 
      },
      { status: 500 }
    );
  }
}