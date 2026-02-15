'use server';

import { createSession, deleteSession, getAccessToken } from '@/lib/session';
import { redirect } from 'next/navigation';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

export type LoginState = {
  error?: string;
  success?: boolean;
};

export async function loginAction(
  prevState: LoginState,
  formData: FormData
): Promise<LoginState> {
  const username = formData.get('username') as string;
  const password = formData.get('password') as string;

  // Validation
  if (!username || !password) {
    return { error: 'Username and password are required' };
  }

  const result = await login(formData);
  return result; // { success: true } or { error: "..." }
}


export async function login(formData: FormData) {
  const username = formData.get('username') as string;
  const password = formData.get('password') as string;

  try {
    const response = await fetch(`${FASTAPI_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        username,
        password,
        grant_type: 'password',
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return {
        error: error.detail || 'Invalid credentials',
      };
    }

    const data = await response.json();

    // Store tokens in session
    await createSession(
      data.access_token,
      data.refresh_token,
      data.expires_in
    );

    return { success: true };
  } catch (error) {
    console.error('Login error:', error);
    return { error: 'An error occurred during login' };
  }
}

export async function logout() {
  await deleteSession();
  redirect('/login');
}

export async function getCurrentUser() {
  const accessToken = await getAccessToken();

  if (!accessToken) {
    return null;
  }

  try {
    const response = await fetch(`${FASTAPI_URL}/users/me`, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      return null;
    }

    return response.json();
  } catch (error) {
    console.error('Get current user error:', error);
    return null;
  }
}

export async function isAuthenticated(): Promise<boolean> {
  const accessToken = await getAccessToken();
  return accessToken !== null;
}
