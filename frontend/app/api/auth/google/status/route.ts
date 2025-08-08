import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/utils/supabase/server';
import { googleAuth } from '@/lib/google-auth';

export async function GET(request: NextRequest) {
  try {
    // Get authenticated user from Supabase
    const supabase = await createClient();
    const { data: { user }, error: userError } = await supabase.auth.getUser();
    
    if (userError || !user) {
      return NextResponse.json({
        authenticated: false,
        message: 'User not logged in to the application'
      });
    }

    // Check if Gmail is connected
    const testResult = await googleAuth.testConnection(user.email!);
    
    if (testResult.connected) {
      return NextResponse.json({
        authenticated: true,
        email: testResult.profile?.emailAddress || user.email,
        profile: testResult.profile,
        message: 'Gmail is connected'
      });
    }

    // Check if tokens exist but connection failed
    const tokens = await googleAuth.loadTokens(user.email!);
    
    if (tokens) {
      // Tokens exist but connection failed - might be expired
      return NextResponse.json({
        authenticated: false,
        hasTokens: true,
        needsReauth: true,
        message: 'Gmail authentication expired. Please re-authenticate.',
        error: testResult.error
      });
    }

    // No tokens found
    return NextResponse.json({
      authenticated: false,
      hasTokens: false,
      needsReauth: false,
      message: 'Gmail not connected. Please authenticate first.'
    });

  } catch (error: any) {
    console.error('Status check error:', error);
    
    return NextResponse.json({
      authenticated: false,
      error: error.message || 'Failed to check authentication status',
      message: 'Error checking Gmail connection'
    }, { status: 500 });
  }
}