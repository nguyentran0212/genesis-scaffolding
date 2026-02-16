import { NextRequest } from 'next/server';
import { apiFetch } from '@/lib/api-client';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

export async function GET(
  request: NextRequest,
  { params }: { params: { proxy: string[] } }
) {
  const path = params.proxy.join('/');
  const searchParams = request.nextUrl.searchParams.toString();
  const endpoint = `/${path}${searchParams ? `?${searchParams}` : ''}`;

  try {
    const response = await apiFetch(endpoint, { method: 'GET' });
    const data = await response.json();

    return Response.json(data, { status: response.status });
  } catch (error) {
    return Response.json(
      { error: 'Proxy request failed' },
      { status: 500 }
    );
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: { proxy: string[] } }
) {
  const path = params.proxy.join('/');
  const body = await request.text();

  try {
    const response = await apiFetch(`/${path}`, {
      method: 'POST',
      body,
      headers: {
        'Content-Type': request.headers.get('Content-Type') || 'application/json',
      },
    });

    const data = await response.json();
    return Response.json(data, { status: response.status });
  } catch (error) {
    return Response.json(
      { error: 'Proxy request failed' },
      { status: 500 }
    );
  }
}
