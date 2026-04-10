# Painful Bugs We Solved

A log of bugs, their symptoms, root causes, and fixes. Updated as problems are discovered and solved.

---

## 2026-04-08: Cookie `secure` Flag Breaking Login via Tailscale HTTP

### Symptoms

- Login works from `localhost` on the same machine
- Login fails from a phone via Tailscale (same network, accessing via tailnet address)
- On the phone, after entering correct credentials, the browser redirects back to login
- Server-side logs show successful token generation (access + refresh tokens issued)
- Middleware logs show subsequent `/dashboard` request has no cookies at all
- Dev mode (`next dev`) works fine; production mode (`next start` via `make run`) fails

### Root Cause

In `lib/session.ts`, session cookies were set with:

```typescript
secure: process.env.NODE_ENV === 'production',
```

In production mode, `NODE_ENV === 'production'` is `true`, so `secure: true` was set on cookies. Browsers refuse to send `secure: true` cookies over HTTP — they require HTTPS.

When accessing via Tailscale with `http://tail-address:3000`, the request is HTTP, so the browser discarded the `secure: true` cookies and never sent them back.

In dev mode, `secure: false`, so cookies worked over HTTP.

### The Fix

Changed `lib/session.ts` to detect the actual request protocol instead of relying on `NODE_ENV`:

```typescript
import { cookies, headers } from 'next/headers';

export async function createSession(accessToken: string, refreshToken: string, expiresIn: number) {
  const cookieStore = await cookies();
  const headersList = await headers();
  // Check if request is over HTTPS (including behind reverse proxies)
  // x-forwarded-proto is set by most reverse proxies (nginx, tailscale exit node, etc.)
  const forwardedProto = headersList.get('x-forwarded-proto') || 'http';
  const isHttps = forwardedProto === 'https';
  // Only set secure=true if actually over HTTPS, not just because NODE_ENV=production
  // This allows HTTP access in production when behind reverse proxies or direct connections

  cookieStore.set('access_token', accessToken, {
    httpOnly: true,
    secure: isHttps,
    sameSite: 'lax',
    maxAge: expiresIn,
    path: '/',
  });

  cookieStore.set('refresh_token', refreshToken, {
    httpOnly: true,
    secure: isHttps,
    sameSite: 'lax',
    maxAge: 60 * 60 * 24 * 7, // 7 days
    path: '/',
  });
}
```

### Lesson

Never set `secure: true` based solely on `NODE_ENV`. Always detect the actual protocol of the incoming request via `x-forwarded-proto` or similar headers. The `NODE_ENV=production` heuristic assumes HTTPS everywhere, which is not true when accessing via Tailscale or other HTTP tunnels.

---

## Backend `datetime` → JavaScript Date Comparisons

### The Problem

Backend `datetime.now(UTC).isoformat()` strips the `Z` suffix, producing strings like `"2026-04-07T01:33:11"` without timezone info. When parsed in JavaScript with `new Date(...)`, this is interpreted as **local time** — not UTC.

This causes comparison bugs when the user's browser is in a timezone other than UTC (e.g., UTC+10:30 Adelaide). For example:

```typescript
// Backend: updated_at = "2026-04-07T01:33:11" (stored as UTC, but isoformat() drops the Z)
// JavaScript parses this as local time: 2026-04-07T01:33:11+10:30
// Date.now() returns UTC:                           2026-04-07T11:33:11Z
// Comparison sees the session as ~10 hours old, not 10 minutes old
```

### The Fix

When comparing a backend datetime field in JavaScript, append `'Z'` to force UTC parsing:

```typescript
// WRONG — parses as local time
const updatedAt = new Date(session.updated_at);

// CORRECT — parses as UTC
const updatedAt = new Date(session.updated_at + 'Z');
```

This applies to any backend datetime stored as UTC and serialized via `.isoformat()`.

---

## `apiFetch` vs Raw `fetch` in Server Actions

### The Problem

In Next.js server actions (functions marked `'use server'`), `fetch` requires an **absolute URL** — relative URLs like `/api/chats` will fail. In client components, browser `fetch` handles relative URLs fine.

The project's `apiFetch` helper (`@/lib/api-client`) sends requests through the Next.js proxy at `/api/*`, which forwards to FastAPI. Using raw `fetch` with a relative path will fail at runtime in server actions.

### The Fix

```typescript
// WRONG — fails in server actions (Node.js fetch needs absolute URL)
const res = await fetch('/api/chats', { method: 'POST', ... });

// CORRECT — routes through Next.js proxy to FastAPI
const res = await apiFetch('/chats/', { method: 'POST', ... });
```

### When to Use Each

| Context | Use |
|---|---|
| Server actions (`'use server'`) | `apiFetch('/chats/...')` — routes through proxy |
| Client components | `apiFetch('/chats/...')` — also routes through proxy |
| External URLs (e.g., webhooks) | Raw `fetch` with absolute URL |

Note: The existing `StartChatButton` in `components/dashboard/start-chat-button.tsx` uses raw `fetch('/api/chats', ...)` — this works only because it is a client component, not a server action. It should be migrated to use `apiFetch` for consistency.
