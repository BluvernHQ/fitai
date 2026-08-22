# FitAI API

FastAPI backend for **FMS → needs → weekly prescription → coach edit → athlete delivery**. Rules-first program assembly with optional Groq enrichment for coach notes only.

**Repository:** [BluvernHQ/fitai](https://github.com/BluvernHQ/fitai)  
**Branch:** `latest`

Pair with the React UI on branch **`latest-ui`**.

---

## What it does

| Capability | Description |
|------------|-------------|
| **FMS analysis** | 7-screen scores, status (STOP → POWER), needs + safety restrictions |
| **Prescription** | `assemble_weekly_program` fills methodology slots from exercise catalog |
| **Periodization** | 4-week mesocycle; weeks 2–4 scale week 1; week 4 deload |
| **Coach edits** | Swap candidates, edit sets/load, taste priors from keep/replace |
| **1RM log** | Append-only history on profile PATCH (coach / test / estimated) |
| **Athlete snapshot** | days, kit, lift_maxes stamped onto program JSON at generate |
| **Share / export** | Public token, HTML print, XLSX, PDF |

Groq (`GROQ_API_KEY`) is **optional** — only rewrites `needs_summary` and per-exercise cues in `enrich_coach_notes`. It cannot add exercises or change loads.

---

## Tech stack

- Python 3.11+, FastAPI, Uvicorn
- SQLAlchemy async (PostgreSQL or SQLite)
- Firebase Auth verification for coaches
- Optional Firestore mirror
- LangChain + Groq for note enrichment
- openpyxl / reportlab for exports

---

## Project structure

```text
fitai/
├── main.py                 # FastAPI app + routes
├── init_db.py              # create tables
├── requirements.txt
├── .env.example
├── data/
│   ├── raw/                # source spreadsheets
│   └── processed/
│       ├── exercise_catalog.json
│       ├── fms_spec.json
│       └── methodology.json
├── src/
│   ├── database.py         # models (Coach, Student, LiftMaxLog, ProgramDraft, …)
│   ├── auth.py             # Firebase token → coach
│   ├── logic/
│   │   ├── fms_analyzer.py
│   │   ├── needs_engine.py
│   │   ├── prescription.py
│   │   ├── periodization.py
│   │   ├── catalog_enrich.py
│   │   ├── taste.py
│   │   └── delivery.py     # export + athlete DTO
│   ├── rag/generator.py    # optional Groq notes
│   └── store/              # optional Firestore
├── scripts/                # ingest / maintenance
└── tests/
```

---

## Environment

Copy `.env.example` to `.env`:

```env
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-120b
GOOGLE_APPLICATION_CREDENTIALS=
FIREBASE_PROJECT_ID=fitai-54f2c
DATA_STORE=sql
FIRESTORE_DATABASE=(default)
CORS_ORIGINS=http://localhost:5173,https://fitai-54f2c.web.app
PORT=8000
```

Never commit `.env`.

---

## Run locally

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # fill secrets
python init_db.py                 # first run / new DB
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

- API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- UI (separate checkout): `latest-ui` branch → `npm run dev` on `:5173`

---

## Core API routes

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/fms/spec` | FMS screen definitions |
| GET | `/methodology` | Slot templates, recovery presets |
| POST | `/students` | Enroll athlete |
| PATCH | `/students/:id` | Profile + 1RMs (logs changes) |
| GET | `/students/:id/lift-maxes/history` | 1RM audit trail |
| POST | `/students/:id/assessments` | Save FMS |
| POST | `/generate-program` | Build week 1 + block |
| PATCH | `/students/:id/workouts/:id` | Coach review events |
| GET | `/public/programs/:token` | Athlete read-only plan |

All coach routes require `Authorization: Bearer <Firebase ID token>`.

---

## Prescription pipeline

```
FMS profile
    → fms_analyzer (scores + status)
    → needs_engine (needs + restrictions)
    → assemble_weekly_program (catalog + methodology + kit + 1RMs)
    → enrich_coach_notes (optional Groq)
    → athlete_snapshot stamped on plan JSON
    → ProgramDraft saved (draft)
```

Later block weeks: `apply_week_progression(week1, n)` — scales volume/intensity, does **not** re-pick exercises.

---

## Data model highlights

- **Student** — profile, days_per_week, equipment, injuries
- **LiftMax** — current 1RM per lift key
- **LiftMaxLog** — append-only history (date, lift, kg, source, previous)
- **Assessment** — raw FMS JSON + computed scores/needs
- **ProgramDraft** — ai_plan / coach_plan JSON, block_id, week_index
- **ShareLink** — hashed token for public athlete view

---

## Tests

```bash
pytest tests/
python test_product.py
python test_prescription.py
```

---

## Branches

| Branch | Contents |
|--------|----------|
| `latest` | Current API + engine (this snapshot) |
| `latest-ui` | React coach UI |
| `main` | Prior stable backend |
| `frontend-react` | Prior UI branch |

---

## Author

Bluvern — FitAI coach platform
