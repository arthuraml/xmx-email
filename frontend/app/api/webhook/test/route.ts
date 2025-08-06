import { NextRequest, NextResponse } from 'next/server';

const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || 'http://localhost:8001';
const PYTHON_API_KEY = process.env.API_KEY || 'cefc0ee900bc2234c94e0df6566aa4fe1e1703cc42d64b858347cfa83e03b774';

/**
 * Webhook de teste para verificar conectividade
 */
export async function GET(request: NextRequest) {
  try {
    // Test connection with Python backend
    const headers = {
      'X-API-Key': PYTHON_API_KEY
    };

    const healthCheckResponse = await fetch(
      `${PYTHON_BACKEND_URL}/api/v1/health`,
      { headers }
    );

    let pythonBackendStatus = 'disconnected';
    let pythonBackendData = null;

    if (healthCheckResponse.ok) {
      pythonBackendData = await healthCheckResponse.json();
      pythonBackendStatus = pythonBackendData.status || 'connected';
    }

    return NextResponse.json({
      success: true,
      message: 'Webhook service is working',
      python_backend: {
        url: PYTHON_BACKEND_URL,
        status: pythonBackendStatus,
        data: pythonBackendData
      }
    });

  } catch (error: any) {
    return NextResponse.json({
      success: false,
      message: 'Webhook service error',
      python_backend: {
        url: PYTHON_BACKEND_URL,
        status: 'disconnected',
        error: error.message
      }
    });
  }
}