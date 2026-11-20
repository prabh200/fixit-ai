# FixIt AI — $0 local-first household repair agent

## What works in this MVP
- Household repair categories: appliances, plumbing, electrical, HVAC, roofing, carpentry, pest control, general maintenance.
- Optional photo + symptom description sent to a local Ollama vision model.
- Structured repair triage.
- Deterministic emergency keyword escalation before normal model diagnosis.
- Safe-check guidance and professional referral flags.
- Clearly labeled illustrative repair cost ranges.
- Live Google Maps / OpenStreetMap search links (no paid map API).
- SQLite repair request storage.
- Cognee persistent memory integration with SQLite fallback.
- Local deterministic evaluation smoke tests.

## Safety and scope
This is an informational prototype, not a licensed contractor or emergency service. It does not confirm faults, verify contractor credentials, make bookings, or contact providers. Never rely on it for gas, fire, electrical, structural, or other dangerous situations. Follow local emergency guidance and qualified professionals.

## Prerequisites
- macOS, Python 3.10–3.12 recommended for dependency compatibility.
- Node.js 20+ for Vite (Guild CLI separately requires Node 22+).
- Ollama installed and running.
- Model: `qwen2.5vl:3b`.

## 1. Start Ollama
```bash
ollama --version
ollama pull qwen2.5vl:3b
ollama serve
```
If Ollama is already running as a Mac app, do not start a second `ollama serve`.

## 2. Backend
Open a terminal:
```bash
cd fixit-ai/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```
First Cognee use may download local extraction and embedding models. This can take time. The backend saves each repair to SQLite even if Cognee setup fails.

If Cognee's first run is too slow for the live demo, set `COGNEE_ENABLED=false` in `backend/.env`; the product will use SQLite memory. For sponsor judging, only describe Cognee as active when the API response says `"provider": "cognee"`.

## 3. Frontend
Open another terminal:
```bash
cd fixit-ai/frontend
npm install
npm run dev
```
Open the Vite URL, normally http://localhost:5173.

## 4. Smoke tests
In the backend terminal with the venv active:
```bash
cd fixit-ai/backend
python evaluate.py
```

## 5. API docs
Open http://localhost:8000/docs

## 6. Two-person split
- Person A: frontend and UX in `frontend/`.
- Person B: backend, Ollama, Cognee, and evaluation in `backend/`.
- Integrate frequently; do not edit the same files simultaneously.

## 7. Guild.ai
See `guild/README.md`. Guild access is not assumed free; use it only if the event sponsor provides a no-cost participant workspace/credits. Do not claim integration until a Guild session/trace is produced.

## No-cost design
No OpenAI/Gemini API keys, paid map API, paid database, cloud hosting, or paid subscription is required. The local AI model and Cognee memory run on the Mac. External map search links require internet access but no API key.
