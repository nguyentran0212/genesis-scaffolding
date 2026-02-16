# Frontend Documentation: Architecture and Structure

## Architecture Overview: Backend-for-Frontend (BFF)

The frontend is designed as a **Backend-for-Frontend (BFF)**. Next.js does not serve as a standalone application but as an orchestration layer between the browser and the FastAPI backend (`myproject-server`).

### Key Design Principles

* **Server-Side Logic:** Authentication, session management, and sensitive API interactions are handled on the server.
* **Server Actions over REST:** Interaction with the backend is primarily driven by Next.js **Server Actions**. This removes the need to expose backend REST endpoints to the client and simplifies state management by moving the "fetch-and-mutate" logic to the server.
* **Environment Isolation:** The `FASTAPI_URL` is kept on the server. The client communicates with the backend either through Server Actions or a dedicated proxy route (`/api/proxy`), preventing the leakage of internal infrastructure details.
* **Stateless Frontend:** Identity is verified by the FastAPI service. The Next.js server maintains a stateless session via HTTP-only cookies, passing JWTs to the backend for authorization.

---

## Technical Stack and Dependencies

The frontend utilizes a modern React ecosystem focused on type safety and performance.

| Category | Technology |
| --- | --- |
| **Framework** | Next.js 16 (App Router) |
| **Language** | TypeScript ^5 |
| **UI Library** | React 19.2 |
| **Styling** | Tailwind CSS 4 (PostCSS build) |
| **UI Components** | Shadcn UI (Radix UI primitives) |
| **Icons** | Lucide React |
| **Utilities** | `clsx`, `tailwind-merge` (for dynamic class management) |

---

## Directory Structure

The project follows the Next.js App Router conventions with a domain-driven organization for components and logic.

### `/app` (Routing and Actions)

* **`/actions`**: Contains Server Actions. These functions handle form submissions (e.g., `auth.ts`) and data mutations, interacting directly with the FastAPI backend.
* **`/api/[...proxy]`**: A catch-all route handler. It proxies client-side requests to the FastAPI backend to bypass CORS and hide the backend origin.
* **`/(routes)`**: Directories like `/login` and `/dashboard` define the application's pages.
* **`layout.tsx`**: The root layout providing the global HTML structure and CSS entry points.

### `/lib` (Core Logic)

* **`auth.ts`**: Integration logic for FastAPI OAuth2 Password flow.
* **`session.ts`**: Low-level cookie management for `access_token` and `refresh_token` using `next/headers`.
* **`api-client.ts`**: Utilities for server-side fetching and standardizing requests to the backend.

### `/components` (UI Layer)

* **`/auth`**: Domain-specific components for authentication (e.g., login forms).
* **`/dashboard`**: Domain-specific components for the authenticated user interface.
* **`/ui`**: (Implicit Shadcn location) Low-level, reusable UI primitives.

### `/types`

* Centralized TypeScript definitions. Interfaces here (e.g., `user.ts`, `auth.ts`) mirror the Pydantic models in the FastAPI backend to ensure type safety across the stack.

### Root Configuration

* **`proxy.ts`**: Middleware that intercepts requests for route protection and JWT validation before they reach the App Router.
* **`components.json`**: Configuration for Shadcn UI components.

---

## Authentication Flow

The authentication system is a custom implementation of the **OAuth2 Password Grant** flow. It avoids third-party libraries, relying on FastAPI for credential validation and Next.js Server Actions for session persistence.

### 1. Credential Submission

The client submits the login form via a **Server Action** (`loginAction`). This avoids exposing the FastAPI `/auth/login` endpoint to the browser.

```typescript
// app/actions/auth.ts
export async function loginAction(prevState: LoginState, formData: FormData) {
  const result = await authenticateUser(username, password); // Calls FastAPI
  
  if (result.success) {
    await createSession(result.data.access_token, result.data.refresh_token);
    return { success: true };
  }
}

```

### 2. Stateless Session Management

Tokens are stored in **HTTP-only, Secure cookies**. This ensures that the frontend remains stateless while protecting tokens from client-side JavaScript access (XSS mitigation).

```typescript
// lib/session.ts
export async function createSession(accessToken: string, refreshToken: string) {
  const cookieStore = await cookies();
  cookieStore.set('access_token', accessToken, { httpOnly: true, secure: true, sameSite: 'lax' });
}

```

### 3. Middleware Protection and Proxying

The `proxy.ts` middleware acts as the primary gatekeeper. It intercepts requests to validate token expiration before the request reaches the App Router or the backend.

* **JWT Validation:** Decodes the `access_token` payload to check the `exp` claim.
* **Route Guarding:** Redirects unauthenticated users to `/login` and authenticated users away from auth pages to `/dashboard`.
* **Token Cleanup:** Deletes expired or invalid cookies during the redirection phase.

### 4. Server-Side Identity Verification

For sensitive operations or initial page loads, the server verifies the token against the FastAPI `/users/me` endpoint.

```typescript
// app/actions/auth.ts
export async function getCurrentUser(): Promise<User | null> {
  const accessToken = await getAccessToken();
  if (!accessToken) return null;

  const user = await fetchUser(accessToken); 
  if (!user) {
    await deleteSession(); // Token rejected by backend
    return null;
  }
  return user;
}

```

---

## API Proxy Implementation

The route handler at `app/api/[...proxy]/route.ts` serves as a transparent bridge for client-side components to communicate with the FastAPI backend. This avoids exposing the `FASTAPI_URL` to the client and centralizes header management.

### Mechanism

The handler uses **Dynamic Route Segments** (`[...proxy]`) to capture any nested path following `/api/`. It reconstructs the target endpoint and forwards the request using `apiFetch`.

* **Path Reconstruction**: It joins the path segments and appends the original query string to ensure the request is identical when it reaches the backend.
* **Method Handling**: Separate `GET` and `POST` exports handle different HTTP verbs, forwarding the request body and `Content-Type` headers where applicable.
* **Encapsulation**: Client-side components call `/api/users/profile` instead of `http://backend-host:8000/users/profile`.

```typescript
// Example Client-Side Usage
const response = await fetch('/api/users/me');
const userData = await response.json();

```

### Integration with `apiFetch`

The proxy relies on a utility in `lib/api-client.ts`. This utility is responsible for:

1. Prepending the `FASTAPI_URL` to the request.
2. Injecting the `access_token` from the server-side cookies into the `Authorization` header.
3. Standardizing error handling for server-to-server communication.

---

## Summary of Logic Flow

| Step | Component | Action |
| --- | --- | --- |
| **1. Request** | Browser | Calls `/api/some-endpoint` |
| **2. Intercept** | `proxy.ts` (Middleware) | Validates JWT; redirects to `/login` if expired. |
| **3. Route** | `app/api/[...proxy]` | Captures path and parameters. |
| **4. Fetch** | `lib/api-client.ts` | Attaches `access_token` and calls FastAPI. |
| **5. Response** | Route Handler | Returns FastAPI's JSON and status code to the browser. |

This architecture ensures that the browser never manages tokens directly and never communicates with the backend origin, maintaining a clean separation of concerns and a secure authentication perimeter.
