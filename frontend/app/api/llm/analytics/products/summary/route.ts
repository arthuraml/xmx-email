import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const period = searchParams.get('period') || 'all'
    
    const aiBackendUrl = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000'
    const apiKey = process.env.AI_API_KEY || 'your-api-key'
    
    const response = await fetch(`${aiBackendUrl}/api/v1/analytics/products/summary?period=${period}`, {
      method: 'GET',
      headers: {
        'X-API-Key': apiKey
      }
    })
    
    if (!response.ok) {
      throw new Error('Failed to fetch product summary')
    }
    
    const data = await response.json()
    return NextResponse.json(data)
    
  } catch (error) {
    console.error('Error fetching product summary:', error)
    return NextResponse.json(
      { error: 'Failed to fetch product summary' },
      { status: 500 }
    )
  }
}