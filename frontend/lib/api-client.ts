import { getAccessToken, getRefreshToken, createSession, deleteSession } from '@/lib/session';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: any
  ) {
    super(message);
  }
}

interface FetchOptions extends RequestInit {
  requireAuth?: boolean;
}

export async function apiFetch(
  endpoint: string,
  options: FetchOptions = {}
): Promise<Response> {
  const { requireAuth = true, ...fetchOptions } = options;

  let accessToken = requireAuth ? await getAccessToken() : null;

  const headers = new Headers(fetchOptions.headers);

  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }

  if (!headers.has('Content-Type') && fetchOptions.body) {
    headers.set('Content-Type', 'application/json');
  }

  let response = await fetch(`${FASTAPI_URL}${endpoint}`, {
    ...fetchOptions,
    headers,
  });

  // If 401 and we need auth, try to refresh token
  if (response.status === 401 && requireAuth) {
    const refreshToken = await getRefreshToken();

    if (refreshToken) {
      // Try to refresh the access token
      const refreshed = await refreshAccessToken(refreshToken);

      if (refreshed) {
        // Retry the original request with new access token
        headers.set('Authorization', `Bearer ${refreshed.accessToken}`);
        response = await fetch(`${FASTAPI_URL}${endpoint}`, {
          ...fetchOptions,
          headers,
        });
      } else {
        // Refresh failed, clear session
        await deleteSession();
      }
    }
  }

  return response;
}

async function refreshAccessToken(refreshToken: string): Promise<{ accessToken: string } | null> {
  try {
    const response = await fetch(`${FASTAPI_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      return null;
    }

    const data = await response.json();

    // Update session with new tokens
    await createSession(
      data.access_token,
      data.refresh_token,
      data.expires_in
    );

    return { accessToken: data.access_token };
  } catch (error) {
    console.error('Token refresh failed:', error);
    return null;
  }
}

// Convenience methods
export async function apiGet(endpoint: string, options?: FetchOptions) {
  const response = await apiFetch(endpoint, { ...options, method: 'GET' });

  if (!response.ok) {
    throw new ApiError(
      response.status,
      `API error: ${response.statusText}`,
      await response.json().catch(() => null)
    );
  }

  return response.json();
}

export async function apiPost(
  endpoint: string,
  data?: any,
  options?: FetchOptions
) {
  const response = await apiFetch(endpoint, {
    ...options,
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  });

  if (!response.ok) {
    throw new ApiError(
      response.status,
      `API error: ${response.statusText}`,
      await response.json().catch(() => null)
    );
  }

  return response.json();
}

export async function apiPut(
  endpoint: string,
  data?: any,
  options?: FetchOptions
) {
  const response = await apiFetch(endpoint, {
    ...options,
    method: 'PUT',
    body: data ? JSON.stringify(data) : undefined,
  });

  if (!response.ok) {
    throw new ApiError(
      response.status,
      `API error: ${response.statusText}`,
      await response.json().catch(() => null)
    );
  }

  return response.json();
}

export async function apiDelete(endpoint: string, options?: FetchOptions) {
  const response = await apiFetch(endpoint, { ...options, method: 'DELETE' });

  if (!response.ok) {
    throw new ApiError(
      response.status,
      `API error: ${response.statusText}`,
      await response.json().catch(() => null)
    );
  }

  // DELETE might return no content
  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export async function apiPatch(
  endpoint: string,
  data?: any,
  options?: FetchOptions
) {
  const response = await apiFetch(endpoint, {
    ...options,
    method: 'PATCH',
    body: data ? JSON.stringify(data) : undefined,
  });

  if (!response.ok) {
    throw new ApiError(
      response.status,
      `API error: ${response.statusText}`,
      await response.json().catch(() => null)
    );
  }

  return response.json();
}
