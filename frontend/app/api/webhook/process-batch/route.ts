import { NextRequest, NextResponse } from 'next/server';

interface EmailBatchRequest {
  emails: Array<{
    email_id: string;
    from: string;
    to: string;
    subject: string;
    body: string;
    received_at?: string;
    thread_id?: string;
  }>;
}

/**
 * Webhook para processar múltiplos e-mails em lote
 */
export async function POST(request: NextRequest) {
  try {
    const body: EmailBatchRequest = await request.json();
    const { emails } = body;

    if (!emails || !Array.isArray(emails) || emails.length === 0) {
      return NextResponse.json({
        success: false,
        error: 'Invalid or empty emails array'
      }, { status: 400 });
    }

    console.log(`Processing batch of ${emails.length} emails`);

    const results = [];
    const errors = [];

    // Get the base URL for internal API calls
    const baseUrl = request.nextUrl.origin;

    // Process each email
    for (const email of emails) {
      try {
        const response = await fetch(
          `${baseUrl}/api/webhook/process-email`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(email)
          }
        );

        if (response.ok) {
          const data = await response.json();
          results.push(data);
        } else {
          const errorData = await response.json();
          errors.push({
            email_id: email.email_id,
            error: errorData.error || 'Processing failed'
          });
        }
      } catch (error: any) {
        errors.push({
          email_id: email.email_id,
          error: error.message
        });
      }
    }

    return NextResponse.json({
      success: true,
      total: emails.length,
      processed: results.length,
      failed: errors.length,
      results,
      errors
    });

  } catch (error: any) {
    console.error('Batch processing error:', error);
    return NextResponse.json({
      success: false,
      error: error.message
    }, { status: 500 });
  }
}