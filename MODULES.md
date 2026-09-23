# Plug-and-play modules

Features are registered in two places, then toggled from **Admin → Modules**.

## Add a new module

### 1. API catalog (`fitai/src/logic/modules.py`)

```python
{
    "id": "my-feature",
    "name": "My Feature",
    "description": "What it does.",
    "category": "coach",  # coach | admin | platform
    "scope": "coach",     # coach | admin
    "default_enabled": False,
    "version": "0.1.0",
}
```

Restart API — row is seeded into `platform_modules` on startup.

### 2. UI registry (`fitai-ui/src/modules/registry.js`)

```javascript
{
  id: "my-feature",
  name: "My Feature",
  description: "...",
  category: "coach",
  scope: "coach",
  icon: SomeLucideIcon,
  path: "/coach/my-feature",
  component: lazy(() => import("../components/modules/MyFeature")),
}
```

Routes in `App.jsx` are generated from registry entries with a `path`.

### 3. Build the module UI

Create `src/components/modules/MyFeature.jsx` and export a page component.

## Admin access

Admin uses a **separate auth gate** from coach login:

1. Open `/admin/login` (not the coach login page).
2. Sign in with an admin account (`ADMIN_EMAILS` or promoted coach).
3. Enter the platform **Admin gate key** (`ADMIN_GATE_SECRET` on the API).
4. API returns a short-lived admin session token (`X-Admin-Session`).

Coach dashboard login alone never unlocks `/admin`. Use **Lock admin** to clear the session.

```env
ADMIN_EMAILS=you@example.com
ADMIN_GATE_SECRET=change-me-admin-gate-key
ADMIN_SESSION_TTL_SEC=28800
```

## Add a new module

Set `embedded: true` and `path: null` for features that live inside existing flows (FMS, program editor, profile) rather than standalone routes.
