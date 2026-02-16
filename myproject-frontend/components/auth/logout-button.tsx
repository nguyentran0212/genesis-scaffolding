'use client';

import { useActionState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { logoutAction } from '@/app/actions/auth';
import type { LogoutState } from '@/types/auth';

export default function LogoutButton() {
  const router = useRouter();
  const [state, formAction, isPending] = useActionState<LogoutState, FormData>(
    logoutAction,
    {}
  );

  useEffect(() => {
    if (state.success) {
      router.push('/login');
    }
  }, [state.success, router]);

  return (
    <form action={formAction}>
      {state.error && (
        <p className="text-sm text-red-600 mr-2">{state.error}</p>
      )}
      <button
        type="submit"
        disabled={isPending}
        className="rounded-md bg-red-600 px-4 py-2 text-sm text-white hover:bg-red-700 disabled:bg-red-400 disabled:cursor-not-allowed transition-colors"
      >
        {isPending ? 'Logging out...' : 'Logout'}
      </button>
    </form>
  );
}
