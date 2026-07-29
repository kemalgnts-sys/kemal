# AGENTS.md

## Cursor Cloud specific instructions

### What this repo is
AutoCheck — a remote vehicle-inspection marketplace. Monorepo with three parts:
- `backend/` — FastAPI + MongoDB (Motor). REST API under `/api/*`, static uploads under `/uploads/*`.
- `frontend/` — React 19 (CRA + CRACO, Tailwind). Turkish UI. The primary product to test end-to-end.
- `mobile/` — Expo/React Native client (optional; needs a device/simulator, not usually run in cloud).

`social-media/` is unrelated marketing collateral, not a runnable service. The real product spec is `memory/PRD.md`; root `README.md` is a placeholder.

### Services and how to run them (web E2E scope)
Start these in separate `tmux` sessions. Required trio: MongoDB + backend + frontend.

- MongoDB: `mongod --dbpath /data/db --bind_ip 127.0.0.1 --port 27017` (data dir `/data/db`). Installed system-wide (v8.0). The backend imports `os.environ['MONGO_URL']` at module load, so Mongo must be reachable or uvicorn crashes on startup.
- Backend: `cd backend && . .venv/bin/activate && uvicorn server:app --host 0.0.0.0 --port 8001 --reload`. Health: `GET http://localhost:8001/api/` and `GET /api/health`.
- Frontend: `cd frontend && BROWSER=none yarn start` → http://localhost:3000. Reads `REACT_APP_BACKEND_URL` from `frontend/.env` (set to `http://localhost:8001`).

### Env files (gitignored — not in the repo)
The update script creates them if missing:
- `backend/.env`: `MONGO_URL`, `DB_NAME`, `CORS_ORIGINS`.
- `frontend/.env`: `REACT_APP_BACKEND_URL`, `WDS_SOCKET_PORT=0`.

### Non-obvious gotchas
- `emergentintegrations==0.1.0` (in `backend/requirements.txt`) is NOT on PyPI and is unused in code. Install with `--extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/` (the update script does this). Without the extra index, `pip install -r requirements.txt` fails.
- Backend Python deps live in `backend/.venv`. Always `. backend/.venv/bin/activate` before running backend/tests.
- Chosen backend port is 8001 (not documented in-repo); `frontend/.env` must match it.
- Known app quirk (not an env issue): the "New Inspection Request" form sends `vehicle.mileage` as an empty string when left blank, which the backend rejects with HTTP 422 and the UI shows no error. Enter an actual mileage number to create an inspection.
- Passwords are stored in plaintext and there is no auth middleware (clients pass `buyer_id`/`inspector_id` as query params). Fine for local dev.

### Lint / test / build
- Backend lint: `flake8 backend/server.py` (style warnings are expected/non-blocking). `black`, `isort`, `mypy` are also available in the venv.
- Backend integration tests: `python3 -c "import backend_test,sys; sys.exit(0 if backend_test.AutoCheckAPITester('http://localhost:8001').run_all_tests() else 1)"` (requires Mongo + backend running). `backend_test.py` defaults to a remote URL, so pass the local base URL as shown.
- Frontend lint: runs via CRACO's eslint-webpack-plugin during `yarn start` / `yarn build` (there is no standalone eslint flat config; running `eslint` directly fails).
- Frontend build: `cd frontend && yarn build`.

### Mobile (optional, out of default scope)
`cd mobile && npm install && npm start` (Expo). API base URL is hardcoded in `mobile/src/config/index.js` to a remote host; change it to a reachable backend for local use.
