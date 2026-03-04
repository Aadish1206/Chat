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
            --bg: #0c1322;
            --panel: #141f36;
            --panel-2: #10192d;
            --text: #dbe6ff;
            --muted: #98a8cf;
            --accent: #6bb2ff;
            --accent-2: #4ae1bb;
            --border: #2b3d63;
          }}
          * {{ box-sizing: border-box; }}
          body {{
            margin: 0;
            font-family: "Segoe UI", Roboto, sans-serif;
            color: var(--text);
            background: radial-gradient(circle at top, #1a2c55 0%, var(--bg) 52%);
            min-height: 100vh;
          }}
          .container {{
            max-width: 1200px;
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
          .layout {{
            display: grid;
            grid-template-columns: 1.1fr 0.9fr;
            gap: 14px;
          }}
          .panel {{
            background: linear-gradient(180deg, rgba(255,255,255,0.035), rgba(255,255,255,0.01));
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
            font-size: 0.96rem;
          }}
          textarea {{
            min-height: 110px;
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
          .ghost {{
            background: transparent;
            color: var(--muted);
            border: 1px solid var(--border);
          }}
          .status {{ color: var(--muted); font-size: 0.9rem; }}
          .chat {{
            margin-top: 16px;
            display: grid;
            gap: 10px;
            max-height: 520px;
            overflow: auto;
            padding-right: 4px;
          }}
          .bubble {{
            border-radius: 12px;
            padding: 12px;
            border: 1px solid var(--border);
            white-space: pre-wrap;
            line-height: 1.35;
          }}
          .user {{ background: rgba(91, 140, 255, 0.15); }}
          .assistant {{ background: rgba(76, 224, 179, 0.14); }}
          .meta {{
            margin-top: 12px;
            color: var(--muted);
            font-size: 0.84rem;
          }}
          .details {{
            background: var(--panel-2);
          }}
          .details h3 {{
            margin: 0 0 12px;
            font-size: 1rem;
          }}
          .kv {{
            margin-bottom: 12px;
          }}
          .kv .label {{
            color: var(--muted);
            font-size: 0.8rem;
            margin-bottom: 4px;
          }}
          .code {{
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            font-size: 0.8rem;
            border: 1px solid var(--border);
            border-radius: 10px;
            background: #0a1326;
            padding: 10px;
            overflow: auto;
            max-height: 180px;
            white-space: pre-wrap;
          }}
          .list {{
            margin: 0;
            padding-left: 18px;
          }}
          .list li {{
            margin-bottom: 6px;
          }}
          details {{
            border: 1px solid var(--border);
            border-radius: 10px;
            margin-bottom: 8px;
            background: #0a1326;
            padding: 6px 10px;
          }}
          details summary {{
            cursor: pointer;
            color: var(--muted);
            font-size: 0.88rem;
          }}
          .empty {{
            color: var(--muted);
            font-size: 0.9rem;
            padding: 8px 0;
          }}
          @media (max-width: 760px) {{
            .grid {{ grid-template-columns: 1fr; }}
            .layout {{ grid-template-columns: 1fr; }}
          }}
        </style>
      </head>
      <body>
        <div class='container'>
          <h1 class='title'>Cogentiq Assistant</h1>
          <p class='subtitle'>Run the full domain/org/usecase tool-binding flow and inspect all orchestration details.</p>
          <div class='layout'>
            <div class='panel'>
              <div class='grid'>
                <div class='field'><label for='domain'>Domain</label><select id='domain'>{domains}</select></div>
                <div class='field'><label for='org'>Organization</label><select id='org'>{orgs}</select></div>
                <div class='field'><label for='usecase'>Use Case</label><select id='usecase'>{usecases}</select></div>
              </div>
              <textarea id='msg' placeholder='Ask a question (Shift+Enter for newline)'></textarea>
              <div class='controls'>
                <button id='sendBtn' onclick='send()'>Send</button>
                <button class='ghost' onclick='clearChat()'>Clear</button>
                <span class='status' id='status'>Ready</span>
              </div>
              <div id='chat' class='chat'></div>
              <div id='meta' class='meta'></div>
            </div>
            <div class='panel details'>
              <h3>Last Response Details</h3>
              <div id='detailsBody' class='empty'>Send a message to view sources, tool traces, runtime trace, and composed prompt.</div>
            </div>
          </div>
        </div>
        <script>
          const msg = document.getElementById('msg');
          const domain = document.getElementById('domain');
          const org = document.getElementById('org');
          const usecase = document.getElementById('usecase');
          const sendBtn = document.getElementById('sendBtn');
          const chat = document.getElementById('chat');
          const status = document.getElementById('status');
          const meta = document.getElementById('meta');
          const detailsBody = document.getElementById('detailsBody');
          const history = [];

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
            chat.scrollTop = chat.scrollHeight;
          }}

          function renderList(items) {{
            if (!items || !items.length) return "<div class='empty'>None</div>";
            return "<ul class='list'>" + items.map((x) => `<li>${{String(x)}}</li>`).join('') + "</ul>";
          }}

          function renderToolTraces(traces) {{
            if (!traces || !traces.length) return "<div class='empty'>No tool traces</div>";
            return traces.map((trace, idx) => {{
              const title = `${{idx + 1}}) ${{trace.tool_name || 'unknown'}} (${{trace.latency_ms || 0}}ms)`;
              const payload = JSON.stringify(trace, null, 2);
              return `<details><summary>${{title}}</summary><pre class='code'>${{payload}}</pre></details>`;
            }}).join('');
          }}

          function renderDetails(resp) {{
            const sources = renderList(resp.sources || []);
            const toolsUsed = renderList(resp.tools_used || []);
            const traces = renderToolTraces(resp.tool_traces || []);
            const traceJson = JSON.stringify(resp.trace || {{}}, null, 2);
            const prompt = resp.composed_prompt || "";
            detailsBody.innerHTML = `
              <div class='kv'>
                <div class='label'>Sources</div>
                ${{sources}}
              </div>
              <div class='kv'>
                <div class='label'>Tools Used</div>
                ${{toolsUsed}}
              </div>
              <div class='kv'>
                <div class='label'>Tool Traces</div>
                ${{traces}}
              </div>
              <div class='kv'>
                <div class='label'>Runtime Trace</div>
                <pre class='code'>${{traceJson}}</pre>
              </div>
              <div class='kv'>
                <div class='label'>Composed Prompt</div>
                <pre class='code'>${{prompt}}</pre>
              </div>
            `;
          }}

          function clearChat() {{
            history.length = 0;
            chat.innerHTML = '';
            meta.textContent = '';
            detailsBody.innerHTML = "Send a message to view sources, tool traces, runtime trace, and composed prompt.";
          }}

          async function send() {{
            const question = msg.value.trim();
            if (!question) return;

            bubble(question, 'user');
            msg.value = '';
            status.textContent = 'Thinking...';
            meta.textContent = '';
            sendBtn.disabled = true;

            const payload = {{
              domain: domain.value,
              org: org.value,
              usecase: usecase.value,
              message: question,
              top_n: 5
            }};

            try {{
              const r = await fetch('/chat', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify(payload)
              }});
              const data = await r.json();
              if (!r.ok) {{
                throw new Error(data.detail || 'Request failed');
              }}
              bubble(data.answer || 'No answer returned.', 'assistant');
              history.push({{ question, response: data }});
              renderDetails(data);
              meta.textContent = `Messages: ${{history.length}} | Sources: ${{(data.sources || []).length}} | Tools: ${{(data.tools_used || []).length}}`;
              status.textContent = 'Done';
            }} catch (err) {{
              bubble(`Error: ${{err.message}}`, 'assistant');
              status.textContent = 'Failed';
            }} finally {{
              sendBtn.disabled = false;
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
