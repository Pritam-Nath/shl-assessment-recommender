from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.models import ChatRequest, ChatResponse
from app.recommender import SHLAgent

app = FastAPI(title="Conversational SHL Assessment Recommender")
agent = SHLAgent()


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SHL Assessment Recommender API</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #172033;
      --muted: #5d6980;
      --line: #d9e2ef;
      --panel: #ffffff;
      --soft: #f4f7fb;
      --accent: #0077b6;
      --accent-dark: #024e78;
      --ok: #15803d;
      --code: #101827;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: #eef4f8;
      letter-spacing: 0;
    }
    main {
      min-height: 100vh;
      padding: 48px 20px;
    }
    .shell {
      width: min(1120px, 100%);
      margin: 0 auto;
    }
    .hero {
      display: grid;
      grid-template-columns: minmax(0, 1.15fr) minmax(320px, 0.85fr);
      gap: 28px;
      align-items: stretch;
    }
    .intro, .panel, .endpoint {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 18px 45px rgba(23, 32, 51, 0.08);
    }
    .intro {
      padding: 36px;
    }
    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 20px;
      color: var(--ok);
      font-size: 14px;
      font-weight: 700;
      text-transform: uppercase;
    }
    .dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--ok);
    }
    h1 {
      max-width: 760px;
      margin: 0;
      font-size: clamp(34px, 6vw, 64px);
      line-height: 1.02;
      font-weight: 800;
    }
    .lead {
      max-width: 720px;
      margin: 22px 0 0;
      color: var(--muted);
      font-size: 18px;
      line-height: 1.65;
    }
    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 30px;
    }
    a.button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 44px;
      padding: 0 18px;
      border-radius: 6px;
      color: #ffffff;
      background: var(--accent);
      text-decoration: none;
      font-weight: 700;
    }
    a.button.secondary {
      color: var(--accent-dark);
      background: #e5f4fb;
      border: 1px solid #b7dcec;
    }
    .panel {
      padding: 26px;
      display: grid;
      gap: 18px;
      align-content: start;
    }
    .stat {
      padding: 18px;
      border-radius: 8px;
      background: var(--soft);
      border: 1px solid var(--line);
    }
    .stat span {
      display: block;
      color: var(--muted);
      font-size: 13px;
      font-weight: 700;
      text-transform: uppercase;
    }
    .stat strong {
      display: block;
      margin-top: 6px;
      color: var(--ink);
      font-size: 24px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
      margin-top: 22px;
    }
    .endpoint {
      padding: 24px;
    }
    .method {
      display: inline-flex;
      margin-bottom: 14px;
      padding: 6px 10px;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 800;
      color: #ffffff;
      background: var(--accent-dark);
    }
    .method.post { background: #7c3aed; }
    h2 {
      margin: 0 0 10px;
      font-size: 22px;
    }
    p {
      color: var(--muted);
      line-height: 1.6;
    }
    code, pre {
      font-family: "Cascadia Code", "SFMono-Regular", Consolas, monospace;
    }
    pre {
      overflow: auto;
      margin: 16px 0 0;
      padding: 16px;
      border-radius: 8px;
      color: #dbeafe;
      background: var(--code);
      border: 1px solid #223047;
      font-size: 13px;
      line-height: 1.55;
    }
    .footer {
      margin-top: 22px;
      color: var(--muted);
      font-size: 14px;
      text-align: center;
    }
    @media (max-width: 860px) {
      main { padding: 24px 14px; }
      .hero, .grid { grid-template-columns: 1fr; }
      .intro { padding: 26px; }
      h1 { font-size: 38px; }
    }
  </style>
</head>
<body>
  <main>
    <div class="shell">
      <section class="hero" aria-label="API overview">
        <div class="intro">
          <div class="eyebrow"><span class="dot"></span>API live</div>
          <h1>SHL Assessment Recommender</h1>
          <p class="lead">
            A stateless FastAPI service that recommends SHL Individual Test Solutions from the catalog.
            Use the health endpoint to check readiness and the chat endpoint to get structured recommendations.
          </p>
          <div class="actions">
            <a class="button" href="/health">Check /health</a>
            <a class="button secondary" href="/docs">Open API docs</a>
          </div>
        </div>
        <aside class="panel" aria-label="Service details">
          <div class="stat">
            <span>Status</span>
            <strong>Ready</strong>
          </div>
          <div class="stat">
            <span>Catalog</span>
            <strong>377 SHL items</strong>
          </div>
          <div class="stat">
            <span>Response schema</span>
            <strong>reply + recommendations</strong>
          </div>
        </aside>
      </section>

      <section class="grid" aria-label="Endpoint instructions">
        <article class="endpoint">
          <span class="method">GET</span>
          <h2>/health</h2>
          <p>Use this readiness check before sending conversations to the recommender.</p>
          <pre>curl https://shl-assessment-recommender-xifx.onrender.com/health</pre>
          <pre>{
  "status": "ok"
}</pre>
        </article>

        <article class="endpoint">
          <span class="method post">POST</span>
          <h2>/chat</h2>
          <p>Send the full stateless conversation history. The service returns the next reply and, when ready, 1 to 10 catalog recommendations.</p>
          <pre>curl -X POST https://shl-assessment-recommender-xifx.onrender.com/chat \\
  -H "Content-Type: application/json" \\
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "Hiring a mid-level Java developer who works with stakeholders"
      }
    ]
  }'</pre>
        </article>
      </section>

      <p class="footer">For interactive testing, open <strong>/docs</strong> and run POST /chat from the Swagger UI.</p>
    </div>
  </main>
</body>
</html>
"""


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return agent.respond(request.messages)
