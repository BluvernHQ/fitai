# FitAI — Project documentation (UI)

## System context

FitAI is a coach tool that turns **Functional Movement Screen (FMS)** results into **4-week mesocycle programs** with editable weekly drafts, athlete share links, and export (CSV / XLSX / PDF).

This document describes the **React UI** (`latest-ui` branch). The **FastAPI backend** lives on the `latest` branch of the same repository.

```
┌─────────────────┐     Firebase Auth      ┌──────────────────┐
│  FitAI UI       │ ─────────────────────► │  Firebase        │
│  (React/Vite)   │                        │  Authentication  │
└────────┬────────┘                        └──────────────────┘
         │ Bearer token
         │ /api → FastAPI
         ▼
┌─────────────────┐     PostgreSQL         ┌──────────────────┐
│  FitAI API      │ ◄──────────────────► │  Students, FMS,  │
│  (main.py)      │     optional Firestore│  programs, 1RMs  │
└─────────────────┘                        └──────────────────┘
         │
         ▼
┌─────────────────┐
│ Prescription    │  rules-first: FMS → needs → catalog slots
│ engine          │  Groq only rewrites coach notes (optional)
└─────────────────┘
```

---

## Coach workflow

1. **Enroll** athlete (name, age, gender, default days/week).
2. **Profile** — update name/age/gender/injuries anytime; set days, equipment, 1RMs (used on next generate).
3. **FMS assessment** — mark faults per screen; scores computed in UI (`src/lib/fmsScore.js`) and sent to API.
4. **Generate week** — API builds week 1 + mesocycle envelope; UI shows calendar + sessions.
5. **Edit draft** — change sets, load, swap candidates; save / approve.
6. **Share** — mint read-only link for athlete (`/v/:token`).
7. **Later weeks** — block weeks 2–4 scale week 1 (no re-pick); deload in week 4.

---

## UI modules

| Module | File(s) | Notes |
|--------|---------|-------|
| Auth | `LoginView`, `SignupView`, `authContext` | Firebase email/password |
| Dashboard | `StudentsDashboard`, `StudentCard` | List + enroll modal |
| Profile | `StudentProfile` | Athlete details + plan inputs + 1RM log |
| FMS | `FMSAssessment`, `fmsScore.js` | 7 screens, computed scores |
| Program | `WorkoutResults`, `WeekStrip`, `SessionBoard` | Calendar grid, edit + approve |
| Athlete | `AthleteProgramView`, `ProgramView` | Public read-only |
| History | `ProgressHistory`, `WorkoutDetail` | Past assessments / workouts |

---

## API integration

All authenticated calls use `src/api/clients.js` → `Authorization: Bearer <Firebase ID token>`.

Important endpoints (proxied as `/api/...`):

- `GET/POST /students`, `PATCH /students/:id`
- `GET /students/:id/lift-maxes/history`
- `POST /students/:id/assessments`
- `POST /generate-program`
- `GET/PATCH /students/:id/workouts/:programId`
- `POST /students/:id/workouts/:programId/share`

---

## Branch & release

| Branch | Contents |
|--------|----------|
| `latest-ui` | This React app (current snapshot) |
| `latest` | FastAPI backend + prescription engine |
| `frontend-react` | Previous UI development branch |
| `main` | Backend history / stable API |

When cutting a release, tag both branches or merge into your deployment branch after QA.

---

## Local development checklist

- [ ] Backend running on `:8000` with valid `.env`
- [ ] UI `.env` with Firebase web app keys
- [ ] Coach account created via signup
- [ ] CORS includes `http://localhost:5173`

---

## Author

Bluvern — FitAI coach platform
