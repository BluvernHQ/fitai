# FitAI — Project documentation (API)

Full-stack coach platform: **assess movement → prescribe training → edit → deliver to athlete**.

| Component | Branch | Stack |
|-----------|--------|-------|
| Backend (this tree) | `latest` | FastAPI, PostgreSQL, Firebase Auth |
| Frontend | `latest-ui` | React, Vite, Firebase Hosting |

Repository: **https://github.com/BluvernHQ/fitai**

---

## Architecture

### Rules-first prescription

The engine is **not** LLM-generated programming. LLM usage is limited to natural-language coach cues.

1. **FMS scoring** (`fms_analyzer.py`) — official 0–3 per screen from faults; pain → STOP.
2. **Needs** (`needs_engine.py`) — mobility / stability / pattern / strength / power tags + safety blocks.
3. **Assembly** (`prescription.py`) — methodology slots (ramp, activation, block_a, block_b, accessories) filled from `exercise_catalog.json` filtered by kit, level, restrictions.
4. **Taste** (`taste.py`) — coach keep/replace priors nudge ranking after ~10 similar decisions; never overrides safety.
5. **Periodization** (`periodization.py`) — mesocycle envelope; week 4 deload; calendar recovery notes.

### Optional AI layer

`src/rag/generator.py` → Groq rewrites:
- `needs_summary` (one paragraph)
- per-exercise `coach_note`

It **cannot** change exercise list, sets, reps, or loads.

---

## Coach ↔ API contract

### Profile vs program

| Field | On save | On generate |
|-------|---------|-------------|
| name, age, gender, injuries | Updates immediately | — |
| days_per_week, equipment, lift_maxes | Saved to student | Copied into `athlete_snapshot` on new program |
| Existing program week | Unchanged | — |

### 1RM logging

On `PATCH /students/:id` when a lift value changes:
- Update `lift_maxes` row
- Append `lift_max_logs` with `previous_one_rm`, `source`, `recorded_at`

Sources: `coach`, `test`, `estimated`.

### Program review events

`PATCH /students/:id/workouts/:id` with `event_type`:
- `edit_prescription` — save coach_plan
- `approve_as_is` / `approve_edited` — lock + optional share
- swap events feed taste priors

---

## Calendar model

- **Gym days** — count from `days_per_week` (2–6); programmed sessions.
- **Recovery** — calendar notes (active/passive/rest); not full exercise blocks in current version.
- **STOP** — referral messaging; no training prescription.
- **Week 4** — gym cells become deload tone; volume scaled down.

---

## Firestore mirror (optional)

When `DATA_STORE` / Firebase credentials are set, selected entities mirror to Firestore for mobile or secondary clients. SQL remains source of truth for prescription.

---

## Ingest pipeline

Exercise catalog and methodology JSON are built from spreadsheets under `data/raw/`:

```bash
# see scripts/ for ingest helpers
python -m src.ingest.excel_to_json_mapper  # if configured
```

Processed artifacts live in `data/processed/`.

---

## Security

- Coach routes: Firebase ID token verified in `src/auth.py`
- Public routes: share token only (`/public/programs/:token`)
- Firestore rules (UI repo): coach-scoped writes
- Never commit `.env`, service account JSON, or database dumps

---

## Deployment notes

- Run behind HTTPS with `CORS_ORIGINS` set to UI origin(s)
- PostgreSQL recommended for production (Neon, RDS, etc.)
- Set `GROQ_API_KEY` only if note enrichment is desired
- Run `_ensure_schema()` on startup (migrations via ALTER in lifespan)

---

## Known limitations (current snapshot)

- Export "Why" column may over-simplify fault targeting
- Some catalog load_basis mappings need tightening (push vs squat 1RM)
- POWER slots may appear frequently unless status is MOBILITY/STABILITY/STOP
- Recovery days are notes, not programmed exercise blocks

See UI `PROJECT.md` on branch `latest-ui` for front-end workflow details.

---

## Author

Bluvern — FitAI coach platform
