import { type NextRequest, NextResponse } from 'next/server'
import { updateSession } from '@/utils/supabase/middleware'
import { getRateLimiter, getIdentifier } from '@/lib/rate-limit'

export async function middleware(request: NextRequest) {
  // Apply rate limiting to API routes
  if (request.nextUrl.pathname.startsWith('/api')) {
    // Skip rate limiting for health check endpoints
    if (request.nextUrl.pathname !== '/api/health' && 
        request.nextUrl.pathname !== '/api/webhook/test') {
      
      // Get the appropriate rate limiter for this route
      const rateLimiter = getRateLimiter(request.nextUrl.pathname);
      
      // Get identifier (user email or IP)
      const identifier = getIdentifier(request);
      
      // Check rate limit
      const rateLimitResult = rateLimiter.check(identifier, request.nextUrl.pathname);
      
      if (!rateLimitResult.success) {
        // Return rate limit error
        const response = NextResponse.json(
          { 
            error: 'Too many requests. Please try again later.',
            retryAfter: Math.ceil((rateLimitResult.reset - Date.now()) / 1000)
          },
          { status: 429 }
        );
        
        // Add rate limit headers
        response.headers.set('X-RateLimit-Limit', rateLimitResult.limit.toString());
        response.headers.set('X-RateLimit-Remaining', rateLimitResult.remaining.toString());
        response.headers.set('X-RateLimit-Reset', new Date(rateLimitResult.reset).toISOString());
        response.headers.set('Retry-After', Math.ceil((rateLimitResult.reset - Date.now()) / 1000).toString());
        
        return response;
      }
      
      // Continue with the request but add rate limit headers
      const response = await updateSession(request);
      response.headers.set('X-RateLimit-Limit', rateLimitResult.limit.toString());
      response.headers.set('X-RateLimit-Remaining', rateLimitResult.remaining.toString());
      response.headers.set('X-RateLimit-Reset', new Date(rateLimitResult.reset).toISOString());
      
      return response;
    }
  }
  
  // For non-API routes, just update the session
  return await updateSession(request)
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * Feel free to modify this pattern to include more paths.
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}