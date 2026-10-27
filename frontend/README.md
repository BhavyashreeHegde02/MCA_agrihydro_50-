# Jalachakra — farmer web application

The farmer-facing interface for the Jalachakra crop water requirement and
irrigation decision support system. Next.js 16 (App Router), React 19,
TypeScript, Tailwind CSS 4, shadcn/ui, Recharts, React Hook Form and Zod.

It replaces the Flutter application named in the original architecture
documents. Nothing else in the system changed: the same FastAPI service, the
same PostgreSQL schema, the same ML and FAO-56 engine, the same weather
abstraction.

---

## Running it

### Windows (recommended)

From the repository root, start both services in the correct order:

```powershell
powershell -ExecutionPolicy Bypass -File .\start-dev.ps1
```

The script starts the backend, waits until `http://127.0.0.1:8000/health`
reports healthy, then starts the frontend. It reuses healthy servers already
running and reports when a different process is occupying either required port.
Open <http://localhost:3000>. Leave both server terminal windows open while
using the app; close them or press Ctrl+C in each to stop the servers.

For a first-time setup, run these commands from the repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Set-Location frontend
npm install
if (-not (Test-Path .env.local)) { Copy-Item .env.example .env.local }
Set-Location ..
```

### Manual start

The backend must be running first — this application has no data of its own.
In PowerShell, open two terminals at the repository root.

Backend terminal:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

Wait for `http://127.0.0.1:8000/health` to return `"status": "ok"`. Then start
the frontend in the second terminal:

```powershell
Set-Location frontend
npm run dev -- --hostname 127.0.0.1 --port 3000
```

The frontend's `.env.local` must contain
`BACKEND_URL=http://127.0.0.1:8000`. In development the backend seeds a demo
account and prints its credentials to its own log.

Access tokens last 15 minutes and are refreshed automatically while the
seven-day refresh-token cookie is valid. Configure a stable, random `SECRET_KEY`
in `backend/.env` to keep sessions valid across backend restarts. Keep that file
private and out of source control. If no key is configured, the backend
generates one at startup, so restarting it invalidates existing tokens and you
must sign in again.

### Environment

| variable | purpose |
|---|---|
| `BACKEND_URL` | where the FastAPI service lives. **Server-side only** — it is never compiled into the browser bundle. |
| `BACKEND_TIMEOUT_MS` | how long to wait before reporting the backend as unresponsive. |
| `COOKIE_SECURE` | `true` when serving over HTTPS. A `Secure` cookie is never stored over plain http, so this must stay `false` locally. |

There is no `NEXT_PUBLIC_` variable holding an API address or a secret, by
design.

---

## Checks

```bash
npm run typecheck && npm run lint && npm run test && npm run build
```

All four must pass. `npm run test` runs Vitest with React Testing Library.

---

## How it is put together

```
src/
  app/
    (auth)/            sign in, register
    (app)/             everything behind a session
    api/
      auth/            login, register, logout, expired  — these set cookies
      proxy/[...path]  authenticated passthrough to the backend
  components/
    ui/                shadcn primitives plus this project's own layer
    charts/            Recharts wrappers
  lib/
    api/               generated types, the client, the server client, errors
    validation/        Zod schemas mirroring the backend's constraints
  proxy.ts             route protection (Next 16 renamed middleware to proxy)
```

### Types come from the backend, not from memory

`src/lib/api/schema.d.ts` is generated from the FastAPI service's own OpenAPI
document. It is not hand-written and should not be edited.

```bash
npm run api:spec     # fetch openapi.json from a running backend
npm run api:types    # regenerate schema.d.ts
```

If a field is renamed in FastAPI, `npm run typecheck` fails here rather than
the interface quietly sending the wrong shape. `openapi.json` is committed so
the build works without the backend running.

The form validation bounds in `src/lib/validation/schemas.ts` are checked
against that committed spec by a test, so widening a rule in the backend
without updating the form fails a test instead of producing a form that
rejects input the backend would have accepted.

### The browser never holds a token

Sign-in posts to this application's own `/api/auth/login`, which exchanges the
credentials with the backend and stores the access and refresh tokens in
**httpOnly** cookies. Every subsequent call goes to `/api/proxy/...`, which
attaches the token server-side and transparently refreshes it once on a 401.

Consequences worth knowing:

- `document.cookie`, `localStorage` and `sessionStorage` are all empty. A
  script injected into the page cannot read or exfiltrate the session.
- `BACKEND_URL` never reaches the client bundle.
- A rejected session leaves through `/api/auth/expired`. That indirection is
  not decoration: a server component can read cookies but cannot set them, so
  redirecting straight to `/login` would leave the dead cookie in place,
  `proxy.ts` would treat the visitor as signed in, and the two would redirect
  at each other until the browser gave up.

### Four states, everywhere

Every screen renders loading, error, empty and content — `LoadingState`,
`ErrorState`, `EmptyState` in `src/components/ui/states.tsx`. A farmer must
always be able to tell a slow network from a broken feature, and an empty
table from a failed request.

### What the numbers mean

The interface never collapses the water figures into one "water needed"
number, because they are four different quantities:

| | meaning |
|---|---|
| **ET₀** | what a reference grass surface would use — weather only |
| **ETc / CWR** | what *this* crop will transpire — ET₀ × Kc |
| **net irrigation** | what must reach the root zone, after rainfall |
| **gross irrigation** | what must be *delivered* — always the largest |

`IrrigationBreakdown` shows that chain step by step with its arithmetic, so
the final figure can be checked rather than trusted.

---

## Things deliberately not done

**The weekly figure is today's value multiplied by seven**, and says so. A
`forecast_7d` task exists in the research code but no model is trained for it;
presenting this as a forecast would be inventing a capability.

**`SelectField` is a native `<select>`, not shadcn's Radix Select.** Radix
renders a button and a portal with no form-associated element, so
`register()` cannot bind to it without a `Controller` per field — and a native
select is the full-screen picker a low-end Android phone gives you.

**The field page is nested under its farm** (`/farms/[farmId]/fields/[fieldId]`)
because the backend has `PUT` and `DELETE` for `/fields/{id}` but no `GET`, so
a field can only be read from its farm's list.
