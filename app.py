from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from cogentiq.knowledge import Knowledge
from runtime.orchestrator import ChatbotRuntime
from runtime.utils import load_env_file, setup_logging

load_env_file()
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
    <!doctype html>
    <html>
      <head>
        <meta charset='utf-8' />
        <meta name='viewport' content='width=device-width, initial-scale=1' />
        <title>Cogentiq Chatbot</title>
        <style>
          :root {{
            --bg: #0b1220;
            --panel: #111a2e;
            --text: #d8e2ff;
            --muted: #8fa2cc;
            --accent: #5b8cff;
            --accent-2: #4ce0b3;
            --border: #2a3657;
          }}
          * {{ box-sizing: border-box; }}
          body {{
            margin: 0;
            font-family: Inter, Segoe UI, Roboto, sans-serif;
            color: var(--text);
            background: radial-gradient(circle at top, #152447 0%, var(--bg) 45%);
            min-height: 100vh;
          }}
          .container {{
            max-width: 980px;
            margin: 0 auto;
            padding: 28px 16px 40px;
          }}
          .title {{
            margin: 0 0 8px;
            font-size: 2rem;
          }}
          .subtitle {{
            margin: 0 0 22px;
            color: var(--muted);
          }}
          .panel {{
            background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01));
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 16px;
            backdrop-filter: blur(4px);
            box-shadow: 0 14px 30px rgba(0, 0, 0, 0.3);
          }}
          .grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 10px;
          }}
          .field label {{
            display: block;
            font-size: 0.82rem;
            color: var(--muted);
            margin-bottom: 6px;
          }}
          select, textarea {{
            width: 100%;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 10px 12px;
            color: var(--text);
            background: #0a1326;
            outline: none;
          }}
          textarea {{
            min-height: 94px;
            resize: vertical;
            margin-top: 10px;
          }}
          .controls {{
            margin-top: 10px;
            display: flex;
            gap: 10px;
            align-items: center;
          }}
          button {{
            border: none;
            border-radius: 10px;
            background: linear-gradient(90deg, var(--accent), var(--accent-2));
            color: #061127;
            font-weight: 700;
            cursor: pointer;
            padding: 10px 16px;
          }}
          .status {{ color: var(--muted); font-size: 0.9rem; }}
          .chat {{
            margin-top: 16px;
            display: grid;
            gap: 10px;
          }}
          .bubble {{
            border-radius: 12px;
            padding: 12px;
            border: 1px solid var(--border);
            white-space: pre-wrap;
          }}
          .user {{ background: rgba(91, 140, 255, 0.15); }}
          .assistant {{ background: rgba(76, 224, 179, 0.14); }}
          .meta {{
            margin-top: 12px;
            color: var(--muted);
            font-size: 0.84rem;
          }}
          @media (max-width: 760px) {{
            .grid {{ grid-template-columns: 1fr; }}
          }}
        </style>
      </head>
      <body>
        <div class='container'>
          <h1 class='title'>Cogentiq Assistant</h1>
          <p class='subtitle'>Smarter orchestration UI with better readability and quick conversation flow.</p>
          <div class='panel'>
            <div class='grid'>
              <div class='field'><label for='domain'>Domain</label><select id='domain'>{domains}</select></div>
              <div class='field'><label for='org'>Organization</label><select id='org'>{orgs}</select></div>
              <div class='field'><label for='usecase'>Use Case</label><select id='usecase'>{usecases}</select></div>
            </div>
            <textarea id='msg' placeholder='Ask a question (Shift+Enter for a newline)'></textarea>
            <div class='controls'>
              <button onclick='send()'>Send Message</button>
              <span class='status' id='status'>Ready</span>
            </div>
            <div id='chat' class='chat'></div>
            <div id='meta' class='meta'></div>
          </div>
        </div>
        <script>
          const msg = document.getElementById('msg');
          const chat = document.getElementById('chat');
          const status = document.getElementById('status');
          const meta = document.getElementById('meta');

          msg.addEventListener('keydown', (event) => {{
            if (event.key === 'Enter' && !event.shiftKey) {{
              event.preventDefault();
              send();
            }}
          }});

          function bubble(text, klass) {{
            const div = document.createElement('div');
            div.className = `bubble ${{klass}}`;
            div.textContent = text;
            chat.appendChild(div);
          }}

          async function send() {{
            const question = msg.value.trim();
            if (!question) return;

            bubble(question, 'user');
            msg.value = '';
            status.textContent = 'Thinking...';
            meta.textContent = '';

            const payload = {{
              domain: domain.value,
              org: org.value,
              usecase: usecase.value,
              message: question,
            }};

            try {{
              const r = await fetch('/chat', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify(payload)
              }});
              const data = await r.json();
              bubble(data.answer || 'No answer returned.', 'assistant');
              meta.textContent = `Sources: ${{(data.sources || []).length}} | Tools: ${{(data.tools_used || []).length}}`;
              status.textContent = 'Done';
            }} catch (err) {{
              bubble(`Error: ${{err.message}}`, 'assistant');
              status.textContent = 'Failed';
            }}
          }}
        </script>
      </body>
    </html>
    """
    return HTMLResponse(html)


@app.post("/chat")
async def chat(req: ChatRequest):
    return await runtime.answer_async(req.domain, req.org, req.usecase, req.message, req.top_n)
