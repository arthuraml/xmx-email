import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_AI_URL || 'http://localhost:8000'
const API_KEY = process.env.BACKEND_AI_API_KEY || 'dev-api-key-2024'

export async function GET(request: NextRequest) {
  try {
    // Extract query parameters
    const searchParams = request.nextUrl.searchParams
    const days = searchParams.get('days') || '7'
    
    // Forward request to Python backend
    const response = await fetch(
      `${BACKEND_URL}/api/v1/analytics/costs/daily?days=${days}`,
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
        { error: 'Failed to fetch daily costs', details: error },
        { status: response.status }
      )
    }
    
    const data = await response.json()
    return NextResponse.json(data)
    
  } catch (error) {
    console.error('Error fetching daily costs:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}