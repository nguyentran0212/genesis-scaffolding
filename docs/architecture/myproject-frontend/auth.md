# Frontend Authentication

## Overview

The frontend communicates with the FastAPI backend using JWT-based authentication. The frontend never stores passwords — it exchanges credentials for tokens and uses those tokens on every subsequent request.

## Auth Flow

### Login

1. User submits username and password to `POST /auth/login`
2. Server validates credentials and returns an access token (15-min JWT) and a refresh token (7-day opaque token)
3. Frontend stores both tokens (access in memory, refresh in httpOnly cookie or secure storage)

### Authenticated Requests

All API requests to protected endpoints include the access token in the `Authorization: Bearer <token>` header. The server validates the JWT signature and expiry on each request.

### Token Refresh

When the access token expires (after 15 minutes), the frontend sends the refresh token to `POST /auth/refresh`. The server validates the refresh token and returns a new access token. This happens transparently — the user is not logged out unless the refresh also fails.

### Logout

Frontend clears stored tokens. The server-side refresh token remains valid in the database until explicitly revoked or until its 7-day expiry.

## Frontend Auth State

The frontend manages authentication state in the shared layout or a dedicated auth context. On page load, the layout checks for a valid session and populates the user state accordingly.

## Related Modules

- `myproject_frontend/lib/server/auth` — Auth utilities, token management
- `myproject_frontend/components/layout` — Layout with auth state and navigation
