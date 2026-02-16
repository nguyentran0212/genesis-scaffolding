'use server';

import { createSession, deleteSession, getAccessToken } from '@/lib/session';
import { authenticateUser, fetchUser, validateCredentials } from '@/lib/auth';
import { redirect } from 'next/navigation';
import type { LoginState, LogoutState } from '@/types/auth';
import type { User } from '@/types/user'

export async function loginAction(
  prevState: LoginState,
  formData: FormData
): Promise<LoginState> {
  const username = formData.get('username') as string;
  const password = formData.get('password') as string;

  const validationError = validateCredentials(username, password);
  if (validationError) {
    return { error: validationError };
  }

  const result = await authenticateUser(username, password);

  if (!result.success) {
    return { error: result.error };
  }

  await createSession(
    result.data!.access_token,
    result.data!.refresh_token,
    result.data!.expires_in
  );

  return { success: true };
}

export async function logoutAction(
  prevState: LogoutState
): Promise<LogoutState> {
  try {
    await deleteSession();
    return { success: true };
  } catch (error) {
    console.error('Logout error:', error);
    return { error: 'Failed to logout' };
  }
}

export async function logout() {
  await deleteSession();
  redirect('/login');
}

export async function getCurrentUser(): Promise<User | null> {
  const accessToken = await getAccessToken();

  if (!accessToken) {
    return null;
  }

  return fetchUser(accessToken);
}

export async function isAuthenticated(): Promise<boolean> {
  const accessToken = await getAccessToken();
  return accessToken !== null;
}
