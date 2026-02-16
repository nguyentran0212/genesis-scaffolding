import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getAccessToken } from '@/lib/session';

// Paths that don't require authentication
const PUBLIC_PATHS = ['/login', '/register', '/'];

// Paths that authenticated users shouldn't access
const AUTH_PATHS = ['/login', '/register'];

export async function middleware(request: NextRequest) {
  const accessToken = await getAccessToken();
  const { pathname } = request.nextUrl;

  const isAuthenticated = !!accessToken;

  // Redirect authenticated users away from auth pages
  if (isAuthenticated && AUTH_PATHS.some(path => pathname.startsWith(path))) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  // Redirect unauthenticated users to login (except for public paths)
  if (!isAuthenticated && !PUBLIC_PATHS.some(path => pathname.startsWith(path))) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('from', pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public files (public folder)
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
};
