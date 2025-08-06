import { NextRequest } from 'next/server';

interface RateLimitOptions {
  interval: number; // Time window in milliseconds
  uniqueTokenPerInterval: number; // Max number of unique tokens per interval
}

interface RateLimitStore {
  [key: string]: {
    count: number;
    resetTime: number;
  };
}

class RateLimiter {
  private store: RateLimitStore = {};
  private interval: number;
  private uniqueTokenPerInterval: number;

  constructor(options: RateLimitOptions) {
    this.interval = options.interval;
    this.uniqueTokenPerInterval = options.uniqueTokenPerInterval;
    
    // Clean up expired entries every minute
    setInterval(() => this.cleanup(), 60000);
  }

  private cleanup() {
    const now = Date.now();
    for (const key in this.store) {
      if (this.store[key].resetTime < now) {
        delete this.store[key];
      }
    }
  }

  private getKey(identifier: string, route: string): string {
    return `${identifier}:${route}`;
  }

  check(identifier: string, route: string): { success: boolean; limit: number; remaining: number; reset: number } {
    const now = Date.now();
    const key = this.getKey(identifier, route);
    
    if (!this.store[key] || this.store[key].resetTime < now) {
      // Initialize or reset the counter
      this.store[key] = {
        count: 1,
        resetTime: now + this.interval
      };
      
      return {
        success: true,
        limit: this.uniqueTokenPerInterval,
        remaining: this.uniqueTokenPerInterval - 1,
        reset: this.store[key].resetTime
      };
    }
    
    // Check if limit is exceeded
    if (this.store[key].count >= this.uniqueTokenPerInterval) {
      return {
        success: false,
        limit: this.uniqueTokenPerInterval,
        remaining: 0,
        reset: this.store[key].resetTime
      };
    }
    
    // Increment counter
    this.store[key].count++;
    
    return {
      success: true,
      limit: this.uniqueTokenPerInterval,
      remaining: this.uniqueTokenPerInterval - this.store[key].count,
      reset: this.store[key].resetTime
    };
  }
}

// Create rate limiters for different endpoints
const rateLimiters = {
  // Gmail API endpoints - 10 requests per minute per user
  gmail: new RateLimiter({
    interval: 60 * 1000, // 1 minute
    uniqueTokenPerInterval: 10
  }),
  
  // Auth endpoints - 5 requests per minute per IP
  auth: new RateLimiter({
    interval: 60 * 1000, // 1 minute
    uniqueTokenPerInterval: 5
  }),
  
  // Webhook endpoints - 100 requests per minute per IP
  webhook: new RateLimiter({
    interval: 60 * 1000, // 1 minute
    uniqueTokenPerInterval: 100
  }),
  
  // Default - 30 requests per minute per IP
  default: new RateLimiter({
    interval: 60 * 1000, // 1 minute
    uniqueTokenPerInterval: 30
  })
};

export function getRateLimiter(route: string): RateLimiter {
  if (route.includes('/api/gmail')) {
    return rateLimiters.gmail;
  } else if (route.includes('/api/auth')) {
    return rateLimiters.auth;
  } else if (route.includes('/api/webhook')) {
    return rateLimiters.webhook;
  }
  return rateLimiters.default;
}

export function getIdentifier(request: NextRequest): string {
  // Try to get user email from cookie or header
  const userEmail = request.cookies.get('user_email')?.value;
  if (userEmail) {
    return userEmail;
  }
  
  // Fall back to IP address
  const forwarded = request.headers.get('x-forwarded-for');
  const ip = forwarded ? forwarded.split(',')[0].trim() : 'unknown';
  return ip;
}

export interface RateLimitResult {
  success: boolean;
  limit: number;
  remaining: number;
  reset: number;
}