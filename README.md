# FitAI UI

Coach-facing web app for **FMS assessment → weekly program generation → review → athlete share**. Built with React, Vite, Tailwind, and Firebase Auth. Talks to the FitAI FastAPI backend via `/api` proxy in dev.

**Repository:** [BluvernHQ/fitai](https://github.com/BluvernHQ/fitai)  
**Branch:** `latest-ui`

---

## What it does

| Area | Description |
|------|-------------|
| **Coach dashboard** | Enroll athletes, open profiles, start assessments |
| **FMS assessment** | Full 7-screen FMS; scores computed from faults (rules-first, not manual taps) |
| **Program week** | Mon–Sun calendar, drag-to-reorder days, edit sets/load, swap exercises, approve |
| **Athlete share** | Read-only public link (`/v/:token`) — no profile editing |
| **Profile** | Name, age, gender, injuries; days/week, kit, 1RMs (apply on **next generate** only) |
| **1RM log** | Date, lift, kg, source (coach / test / estimated) |
| **Progress history** | FMS screens and saved workouts |

---

## Tech stack

- React 19, React Router 7, Vite 7
- Tailwind CSS 4, Framer Motion, Lucide
- Firebase Authentication (email/password)
- Firebase Hosting + Firestore rules (optional mirror from API)

---

## Project structure

```text
fitai-ui/
├── src/
│   ├── api/              # backend.js, clients.js, fms.js
│   ├── components/       # pages and UI (FMS, program, profile, …)
│   ├── context/          # authContext
│   ├── firebase/         # config + auth helpers
│   ├── lib/              # fmsScore.js, programView.js
│   └── App.jsx           # routes
├── shared/fms-spec/      # FMS spec JSON (shared with backend)
├── firestore.rules       # Firestore security rules
├── firebase.json         # Hosting + Firestore config
├── vite.config.js        # dev proxy /api → backend :8000
└── .env.example          # copy to .env (never commit .env)
```

---

## Environment

Copy `.env.example` to `.env`:

```env
VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=
VITE_FIREBASE_PROJECT_ID=
VITE_FIREBASE_APP_ID=
# optional — defaults to http://127.0.0.1:8000
# VITE_RAG_PROXY=http://127.0.0.1:8000
```

Firebase client keys are public by design; restrict access with Firebase Auth + Firestore rules.

---

## Run locally

**1. Backend** (separate clone / `fitai` repo, branch `latest`):

```bash
cd fitai
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill DATABASE_URL, GROQ_API_KEY, etc.
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**2. UI:**

```bash
cd fitai-ui
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). API calls go to `/api/*` → `127.0.0.1:8000`.

---

## Deploy (Firebase Hosting)

```bash
npm run build
firebase deploy
```

Ensure backend `CORS_ORIGINS` includes your Hosting URL.

---

## Key routes

| Path | Role |
|------|------|
| `/` | Login |
| `/coach/dashboard` | Student list |
| `/coach/student/:id` | Profile + plan inputs + 1RM log |
| `/coach/student/:id/fms` | FMS assessment |
| `/coach/student/:id/program/:programId` | Program editor |
| `/v/:token` | Athlete read-only share |

---

## Product rules (UI)

- **Profile fields** (days, kit, 1RMs) are inputs for the **next generate**, not live edits to the current week.
- **Athlete share** cannot edit profile or program structure.
- **1RM history** lives on the coach profile; Progress History is FMS + workouts only.

---

## Related repo

Backend API, prescription engine, and exports: same GitHub repo, branch **`latest`** (`fitai/` directory when checked out from that branch).
