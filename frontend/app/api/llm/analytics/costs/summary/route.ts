import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_AI_URL || 'http://localhost:8000'
const API_KEY = process.env.BACKEND_AI_API_KEY || 'dev-api-key-2024'

export async function GET(request: NextRequest) {
  try {
    // Extract query parameters
    const searchParams = request.nextUrl.searchParams
    const period = searchParams.get('period') || 'today'
    
    // Forward request to Python backend
    const response = await fetch(
      `${BACKEND_URL}/api/v1/analytics/costs/summary?period=${period}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY
        }
      }
    )
    
    if (!response.ok) {
      const error = await response.text()
      return NextResponse.json(
        { error: 'Failed to fetch cost summary', details: error },
        { status: response.status }
      )
    }
    
    const data = await response.json()
    return NextResponse.json(data)
    
  } catch (error) {
    console.error('Error fetching cost summary:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}