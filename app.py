from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from cogentiq.knowledge import Knowledge
from runtime.orchestrator import ChatbotRuntime
from runtime.utils import setup_logging

setup_logging()
app = FastAPI(title="Cogentiq Domain Layer Chatbot")
runtime = ChatbotRuntime("data")
knowledge = Knowledge("data")


class ChatRequest(BaseModel):
    domain: str
    org: str
    usecase: str
    message: str
    top_n: int = 5


@app.get("/")
def home() -> HTMLResponse:
    domains = "".join([f"<option>{d}</option>" for d in knowledge.domains()])
    orgs = "".join([f"<option>{o}</option>" for o in knowledge.orgs()])
    usecases = "".join([f"<option>{u}</option>" for u in knowledge.usecases()])
    html = f"""
    <html><body>
    <h2>Cogentiq Chatbot</h2>
    <label>Domain</label><select id='domain'>{domains}</select>
    <label>Org</label><select id='org'>{orgs}</select>
    <label>Usecase</label><select id='usecase'>{usecases}</select><br/><br/>
    <textarea id='msg' rows='4' cols='80' placeholder='Ask a question'></textarea><br/>
    <button onclick='send()'>Send</button>
    <pre id='out'></pre>
    <script>
    async function send() {{
      const payload = {{domain: domain.value, org: org.value, usecase: usecase.value, message: msg.value}};
      const r = await fetch('/chat', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body: JSON.stringify(payload)}});
      out.textContent = JSON.stringify(await r.json(), null, 2);
    }}
    </script>
    </body></html>
    """
    return HTMLResponse(html)


@app.post("/chat")
async def chat(req: ChatRequest):
    return await runtime.answer_async(req.domain, req.org, req.usecase, req.message, req.top_n)
