"""
Web UI + /ask endpoint.

    uvicorn app:app --reload
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

import agent

app = FastAPI(title="Private Business Agent")


class Query(BaseModel):
    question: str


@app.post("/ask")
def ask(query: Query):
    result = agent.answer(query.question)
    return JSONResponse(result)


@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Private Business Agent</title>
<style>
  body { font-family: -apple-system, system-ui, sans-serif; max-width: 720px; margin: 40px auto; padding: 0 20px; color: #1a1a1a; }
  h1 { font-size: 1.3rem; }
  #log { border: 1px solid #ddd; border-radius: 8px; padding: 16px; min-height: 300px; margin-bottom: 12px; white-space: pre-wrap; }
  .q { font-weight: 600; margin-top: 14px; }
  .a { margin-top: 6px; color: #333; }
  .plan { font-size: 0.8rem; color: #888; margin-top: 4px; }
  form { display: flex; gap: 8px; }
  input { flex: 1; padding: 10px; border-radius: 6px; border: 1px solid #ccc; }
  button { padding: 10px 16px; border-radius: 6px; border: none; background: #111; color: white; cursor: pointer; }
  .hint { font-size: 0.85rem; color: #888; margin-bottom: 16px; }
</style>
</head>
<body>
<h1>Private Business Agent</h1>
<p class="hint">Try: "Which invoices are overdue?", "What did Apex say about invoice 1042?", "When does the CloudHost contract renew?"</p>
<div id="log"></div>
<form id="f">
  <input id="q" placeholder="Ask about invoices, emails, or contracts..." autofocus />
  <button type="submit">Ask</button>
</form>
<script>
const log = document.getElementById('log');
// textContent, not innerHTML - answers can contain text from documents
function addLine(cls, text) {
  const div = document.createElement('div');
  div.className = cls;
  div.textContent = text;
  log.appendChild(div);
}
document.getElementById('f').addEventListener('submit', async (e) => {
  e.preventDefault();
  const input = document.getElementById('q');
  const question = input.value;
  if (!question) return;
  addLine('q', `You: ${question}`);
  input.value = '';
  const resp = await fetch('/ask', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({question})
  });
  const data = await resp.json();
  addLine('plan', `routed to: ${JSON.stringify(data.plan)}`);
  addLine('a', data.answer);
  log.scrollTop = log.scrollHeight;
});
</script>
</body>
</html>
"""
