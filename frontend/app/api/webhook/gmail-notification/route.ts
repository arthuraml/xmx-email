import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/utils/supabase/server';
import { gmailService } from '@/lib/gmail-service';

interface GmailPushNotification {
  message: {
    data: string; // Base64 encoded message data
    messageId: string;
    publishTime: string;
  };
  subscription: string;
}

interface GmailNotificationData {
  emailAddress: string;
  historyId: string;
}

/**
 * Endpoint para receber notificações do Gmail Push Notifications
 * Quando um novo e-mail chegar, o Gmail chama este webhook
 */
export async function POST(request: NextRequest) {
  try {
    const body: GmailPushNotification = await request.json();
    const { message } = body;
    
    // Decode the message from Gmail
    const messageData: GmailNotificationData = JSON.parse(
      Buffer.from(message.data, 'base64').toString()
    );

    console.log('Gmail notification received:', messageData);

    // Get the user associated with this email address
    const supabase = await createClient();
    
    // Query the oauth_tokens table to find the user with this Gmail address
    const { data: tokenData, error: tokenError } = await supabase
      .from('oauth_tokens')
      .select('user_email, gmail_profile')
      .eq('gmail_profile->>emailAddress', messageData.emailAddress)
      .single();

    if (tokenError || !tokenData) {
      console.error('Could not find user for email:', messageData.emailAddress);
      return NextResponse.json({ status: 'user_not_found' }, { status: 200 });
    }

    const userEmail = tokenData.user_email;

    // Fetch new messages since the last historyId
    // This would require implementing a history sync mechanism
    // For now, we'll just fetch the latest messages
    try {
      const messages = await gmailService.getInboxMessages(userEmail, 5);
      
      if (messages.length > 0) {
        // Process the new messages
        for (const message of messages) {
          // Check if message is unread (new)
          if (message.isUnread) {
            console.log(`Processing new message: ${message.id} - ${message.subject}`);
            
            // Call the process-email webhook to handle the message
            const baseUrl = request.nextUrl.origin;
            await fetch(`${baseUrl}/api/webhook/process-email`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                email_id: message.id,
                from: message.from,
                to: message.to,
                subject: message.subject,
                body: message.body,
                received_at: message.date.toISOString(),
                thread_id: message.threadId
              })
            });
          }
        }
      }

      // Update the stored historyId for future syncs
      await supabase
        .from('oauth_tokens')
        .update({
          gmail_profile: {
            ...tokenData.gmail_profile,
            historyId: messageData.historyId
          },
          updated_at: new Date().toISOString()
        })
        .eq('user_email', userEmail);

    } catch (error: any) {
      console.error('Error processing Gmail notification:', error);
    }

    // Always return 200 to acknowledge receipt
    // Gmail will retry if we don't acknowledge
    return NextResponse.json({ status: 'ok' }, { status: 200 });

  } catch (error: any) {
    console.error('Gmail notification error:', error);
    
    // Still return 200 to prevent Gmail from retrying
    // Log the error for debugging
    return NextResponse.json({ 
      status: 'error_logged',
      error: error.message 
    }, { status: 200 });
  }
}

/**
 * GET endpoint for Gmail to verify the webhook URL
 * Gmail will call this to confirm the webhook is valid
 */
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const challenge = searchParams.get('hub.challenge');
  const mode = searchParams.get('hub.mode');
  const topic = searchParams.get('hub.topic');

  // If this is a verification request from Gmail
  if (mode === 'subscribe' && challenge) {
    console.log('Gmail webhook verification request received');
    console.log('Topic:', topic);
    
    // Echo back the challenge to verify
    return new NextResponse(challenge, {
      status: 200,
      headers: {
        'Content-Type': 'text/plain'
      }
    });
  }

  // Otherwise, just return a status message
  return NextResponse.json({
    status: 'Gmail notification webhook is ready',
    message: 'This endpoint receives push notifications from Gmail'
  });
}