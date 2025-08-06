import { NextRequest, NextResponse } from 'next/server';
import { googleAuth } from '@/lib/google-auth';
import { google } from 'googleapis';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const error = searchParams.get('error');
    
    // Check for OAuth errors
    if (error) {
      console.error('OAuth error:', error);
      return new NextResponse(generateErrorHTML('Authentication was denied or failed'), {
        status: 400,
        headers: { 'Content-Type': 'text/html' }
      });
    }
    
    // Validate authorization code
    if (!code) {
      return new NextResponse(generateErrorHTML('No authorization code received'), {
        status: 400,
        headers: { 'Content-Type': 'text/html' }
      });
    }
    
    // Get user email from cookie
    const userEmail = request.cookies.get('gmail_auth_email')?.value;
    
    if (!userEmail) {
      return new NextResponse(generateErrorHTML('Session expired. Please try again.'), {
        status: 401,
        headers: { 'Content-Type': 'text/html' }
      });
    }
    
    // Exchange code for tokens
    const tokens = await googleAuth.handleCallback(code);
    
    // Get Gmail profile
    const oAuth2Client = new google.auth.OAuth2(
      process.env.GOOGLE_CLIENT_ID!,
      process.env.GOOGLE_CLIENT_SECRET!,
      process.env.NODE_ENV === 'production'
        ? process.env.GOOGLE_REDIRECT_URI_PROD!
        : process.env.GOOGLE_REDIRECT_URI!
    );
    
    oAuth2Client.setCredentials(tokens);
    
    const gmail = google.gmail({ version: 'v1', auth: oAuth2Client });
    const profileResponse = await gmail.users.getProfile({ userId: 'me' });
    
    const gmailProfile = {
      emailAddress: profileResponse.data.emailAddress!,
      messagesTotal: profileResponse.data.messagesTotal,
      threadsTotal: profileResponse.data.threadsTotal,
      historyId: profileResponse.data.historyId
    };
    
    // Save tokens and profile to Supabase
    await googleAuth.saveTokens(userEmail, tokens, gmailProfile);
    
    // Generate success response
    const response = new NextResponse(generateSuccessHTML(gmailProfile.emailAddress), {
      status: 200,
      headers: { 'Content-Type': 'text/html' }
    });
    
    // Clear the email cookie
    response.cookies.delete('gmail_auth_email');
    
    return response;
    
  } catch (error: any) {
    console.error('Callback error:', error);
    
    const errorMessage = error.message || 'An unexpected error occurred during authentication';
    
    return new NextResponse(generateErrorHTML(errorMessage), {
      status: 500,
      headers: { 'Content-Type': 'text/html' }
    });
  }
}

function generateSuccessHTML(email: string): string {
  const frontendUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';
  
  return `
    <!DOCTYPE html>
    <html lang="pt-BR">
      <head>
        <title>Autenticação Concluída</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
          * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
          }
          
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          }
          
          .container {
            text-align: center;
            padding: 3rem;
            background: white;
            border-radius: 1rem;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 450px;
            width: 90%;
          }
          
          .success-icon {
            width: 80px;
            height: 80px;
            margin: 0 auto 1.5rem;
            background: #4CAF50;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: scaleIn 0.3s ease-out;
          }
          
          @keyframes scaleIn {
            from {
              transform: scale(0);
              opacity: 0;
            }
            to {
              transform: scale(1);
              opacity: 1;
            }
          }
          
          .checkmark {
            width: 40px;
            height: 40px;
            stroke: white;
            stroke-width: 3;
            fill: none;
            stroke-dasharray: 100;
            stroke-dashoffset: 100;
            animation: drawCheck 0.5s ease-out 0.3s forwards;
          }
          
          @keyframes drawCheck {
            to {
              stroke-dashoffset: 0;
            }
          }
          
          h1 {
            color: #333;
            font-size: 1.75rem;
            margin-bottom: 0.5rem;
          }
          
          .email {
            color: #666;
            font-size: 1rem;
            margin: 0.5rem 0;
            padding: 0.5rem 1rem;
            background: #f5f5f5;
            border-radius: 0.5rem;
            display: inline-block;
          }
          
          p {
            color: #666;
            margin: 1rem 0;
            line-height: 1.5;
          }
          
          .button {
            display: inline-block;
            padding: 0.75rem 2rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 0.5rem;
            margin-top: 1.5rem;
            font-weight: 500;
            transition: transform 0.2s, box-shadow 0.2s;
          }
          
          .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
          }
          
          .countdown {
            color: #999;
            font-size: 0.875rem;
            margin-top: 1rem;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="success-icon">
            <svg class="checkmark" viewBox="0 0 52 52">
              <path d="M14 27l10 10 20-20" />
            </svg>
          </div>
          <h1>Autenticação Concluída!</h1>
          <div class="email">${email}</div>
          <p>Sua conta do Gmail foi conectada com sucesso ao XMX Email.</p>
          <p>Agora você pode acessar e gerenciar seus emails diretamente pelo aplicativo.</p>
          <a href="${frontendUrl}/llm" class="button">Ir para o Aplicativo</a>
          <p class="countdown">Redirecionando em <span id="timer">5</span> segundos...</p>
        </div>
        <script>
          let seconds = 5;
          const timer = document.getElementById('timer');
          
          const countdown = setInterval(() => {
            seconds--;
            if (timer) timer.textContent = seconds.toString();
            
            if (seconds <= 0) {
              clearInterval(countdown);
              window.location.href = '${frontendUrl}/llm';
            }
          }, 1000);
          
          // Close window if it was opened as a popup
          if (window.opener) {
            window.opener.postMessage({ type: 'auth-success', email: '${email}' }, '*');
            setTimeout(() => {
              window.close();
            }, 5000);
          }
        </script>
      </body>
    </html>
  `;
}

function generateErrorHTML(error: string): string {
  const frontendUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';
  
  return `
    <!DOCTYPE html>
    <html lang="pt-BR">
      <head>
        <title>Erro de Autenticação</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
          * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
          }
          
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: linear-gradient(135deg, #f5576c 0%, #f093fb 100%);
          }
          
          .container {
            text-align: center;
            padding: 3rem;
            background: white;
            border-radius: 1rem;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 450px;
            width: 90%;
          }
          
          .error-icon {
            width: 80px;
            height: 80px;
            margin: 0 auto 1.5rem;
            background: #f44336;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: shake 0.5s ease-out;
          }
          
          @keyframes shake {
            0%, 100% { transform: translateX(0); }
            10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
            20%, 40%, 60%, 80% { transform: translateX(5px); }
          }
          
          .cross {
            width: 40px;
            height: 40px;
            position: relative;
          }
          
          .cross:before,
          .cross:after {
            content: '';
            position: absolute;
            width: 30px;
            height: 3px;
            background: white;
            border-radius: 2px;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(45deg);
          }
          
          .cross:after {
            transform: translate(-50%, -50%) rotate(-45deg);
          }
          
          h1 {
            color: #333;
            font-size: 1.75rem;
            margin-bottom: 1rem;
          }
          
          .error-message {
            color: #666;
            background: #ffebee;
            border: 1px solid #ffcdd2;
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 1rem 0;
            text-align: left;
            font-family: 'Courier New', monospace;
            font-size: 0.875rem;
            word-break: break-word;
          }
          
          p {
            color: #666;
            margin: 1rem 0;
            line-height: 1.5;
          }
          
          .button {
            display: inline-block;
            padding: 0.75rem 2rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 0.5rem;
            margin-top: 1.5rem;
            font-weight: 500;
            transition: transform 0.2s, box-shadow 0.2s;
          }
          
          .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="error-icon">
            <div class="cross"></div>
          </div>
          <h1>Erro de Autenticação</h1>
          <p>Ocorreu um erro durante o processo de autenticação com o Gmail.</p>
          <div class="error-message">${error}</div>
          <p>Por favor, tente novamente ou entre em contato com o suporte se o problema persistir.</p>
          <a href="${frontendUrl}/llm" class="button">Tentar Novamente</a>
        </div>
        <script>
          // Close window if it was opened as a popup
          if (window.opener) {
            window.opener.postMessage({ type: 'auth-error', error: '${error.replace(/'/g, "\\'")}' }, '*');
          }
        </script>
      </body>
    </html>
  `;
}