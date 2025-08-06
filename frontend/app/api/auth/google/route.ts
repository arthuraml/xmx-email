import { NextRequest, NextResponse } from 'next/server';
import { googleAuth } from '@/lib/google-auth';
import { createClient } from '@/utils/supabase/server';

export async function GET(request: NextRequest) {
  try {
    // Check if user is already authenticated with Gmail
    const supabase = await createClient();
    
    // Get current user
    const { data: { user }, error: userError } = await supabase.auth.getUser();
    
    if (userError || !user) {
      return NextResponse.json({
        success: false,
        error: 'User not authenticated. Please login first.'
      }, { status: 401 });
    }

    // Check if Gmail is already connected
    const testResult = await googleAuth.testConnection(user.email!);
    
    if (testResult.connected) {
      return NextResponse.json({
        success: true,
        message: 'Gmail already connected',
        email: testResult.profile?.emailAddress,
        profile: testResult.profile
      });
    }

    // Generate OAuth URL
    const authUrl = googleAuth.getAuthUrl();
    
    // Store state in cookie for CSRF protection
    const response = NextResponse.json({
      success: true,
      message: 'Visit the URL below to authenticate with Gmail',
      authUrl: authUrl,
      instructions: 'After authorizing, you will be redirected back to complete the authentication.'
    });

    // Set HTTP-only cookie with user email for callback
    response.cookies.set('gmail_auth_email', user.email!, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 60 * 10 // 10 minutes
    });

    return response;

  } catch (error: any) {
    console.error('Auth route error:', error);
    return NextResponse.json({
      success: false,
      error: error.message || 'Failed to initiate authentication'
    }, { status: 500 });
  }
}

// POST endpoint to trigger authentication in a new window
export async function POST(request: NextRequest) {
  try {
    const supabase = await createClient();
    
    // Get current user
    const { data: { user }, error: userError } = await supabase.auth.getUser();
    
    if (userError || !user) {
      return NextResponse.json({
        success: false,
        error: 'User not authenticated'
      }, { status: 401 });
    }

    // Generate OAuth URL
    const authUrl = googleAuth.getAuthUrl();
    
    // Store user email in cookie for callback
    const response = NextResponse.json({
      success: true,
      authUrl: authUrl
    });

    response.cookies.set('gmail_auth_email', user.email!, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 60 * 10 // 10 minutes
    });

    return response;

  } catch (error: any) {
    console.error('Auth POST error:', error);
    return NextResponse.json({
      success: false,
      error: error.message || 'Failed to generate auth URL'
    }, { status: 500 });
  }
}