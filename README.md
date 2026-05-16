# Conversational SHL Assessment Recommender

FastAPI service for the SHL AI Intern take-home assignment. It exposes:

- `GET /health`
- `POST /chat`

The app is stateless: every `/chat` request includes the full conversation history. It uses a cached SHL Individual Test Solutions catalog and a deterministic retrieval/ranking agent.

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/scrape_catalog.py
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Example

```bash
curl -X POST http://localhost:8000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"messages\":[{\"role\":\"user\",\"content\":\"Hiring a mid-level Java developer who works with stakeholders\"}]}"
```

## Deploy

Use any FastAPI-friendly host such as Render, Railway, Fly.io, or Hugging Face Spaces. Make sure `data/shl_catalog.json` is committed or run `python scripts/scrape_catalog.py` during build.

### Render

1. Push this folder to a GitHub repository.
2. In Render, create a new Web Service from that repository.
3. Use:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Health check path: `/health`
4. Submit the Render service URL after confirming `/health` and `/chat` work.
