"""
FastAPI application instance. Mounts all routers and runs startup configuration.
Run locally with: uvicorn app.api.main:app --reload
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.api.middleware.auth import APIKeyMiddleware
from app.api.middleware.rate_limit import register_rate_limiter
from app.api.routes import chat, health, messages, proactive
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Shinzo AI starting up")

    # Initialize database (creates tables if not exist)
    try:
        from app.memory.db import init_db
        init_db()
        logger.info("Database initialized.")
    except Exception as exc:
        logger.error("Database init failed: %s", exc)

    # Start proactive scheduler (skip in serverless environments)
    if not (os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")):
        try:
            from app.proactive.scheduler import start_scheduler
            start_scheduler()
        except Exception as exc:
            logger.error("Proactive scheduler failed to start: %s", exc)

    yield

    # Graceful shutdown
    if not (os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")):
        try:
            from app.proactive.scheduler import stop_scheduler
            stop_scheduler()
        except Exception:
            pass

    logger.info("Shinzo AI shutting down")


app = FastAPI(
    title="Shinzo AI",
    version="0.2.0",
    description="Emotionally intelligent AI companion — API",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(APIKeyMiddleware)
register_rate_limiter(app)

# Routes
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(proactive.router)
app.include_router(messages.router)


@app.get("/", response_class=HTMLResponse)
@app.get("/api")
@app.get("/api/index")
async def root(request: Request):
    accept = request.headers.get("accept", "")
    if "text/html" not in accept:
        return JSONResponse({
            "status": "online",
            "service": "Shinzo AI",
            "version": "0.2.0",
            "docs": "/docs",
            "health": "/health",
        })

    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Shinzo AI — Empathetic AI Companion</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #090d16;
            --card-bg: rgba(18, 24, 38, 0.75);
            --card-border: rgba(255, 255, 255, 0.08);
            --accent: #8b5cf6;
            --accent-glow: rgba(139, 92, 246, 0.35);
            --accent-teal: #06b6d4;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --user-bubble: #3b82f6;
            --bot-bubble: rgba(30, 41, 59, 0.85);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', sans-serif;
            background: radial-gradient(circle at top, #1e1b4b 0%, var(--bg) 60%);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            width: 100%;
            max-width: 780px;
            background: var(--card-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--card-border);
            border-radius: 24px;
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.6), 0 0 40px var(--accent-glow);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: 85vh;
        }
        .header {
            padding: 20px 24px;
            border-bottom: 1px solid var(--card-border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(15, 23, 42, 0.5);
        }
        .header-title {
            font-family: 'Outfit', sans-serif;
            font-size: 1.35rem;
            font-weight: 700;
            background: linear-gradient(135deg, #a855f7, #38bdf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 0.8rem;
            color: #34d399;
            background: rgba(52, 211, 153, 0.1);
            border: 1px solid rgba(52, 211, 153, 0.2);
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 500;
        }
        .status-dot {
            width: 7px;
            height: 7px;
            background: #34d399;
            border-radius: 50%;
            box-shadow: 0 0 8px #34d399;
            animation: pulse 2s infinite;
        }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        .docs-link {
            color: var(--text-secondary);
            font-size: 0.85rem;
            text-decoration: none;
            padding: 6px 14px;
            border-radius: 10px;
            border: 1px solid var(--card-border);
            transition: all 0.2s;
        }
        .docs-link:hover {
            color: #fff;
            border-color: var(--accent);
            background: rgba(139, 92, 246, 0.1);
        }
        .chat-box {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .message {
            max-width: 80%;
            padding: 14px 18px;
            border-radius: 18px;
            line-height: 1.5;
            font-size: 0.95rem;
            animation: fadeIn 0.25s ease-out;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
        .user-message {
            align-self: flex-end;
            background: linear-gradient(135deg, #6366f1, #3b82f6);
            color: white;
            border-bottom-right-radius: 4px;
        }
        .bot-message {
            align-self: flex-start;
            background: var(--bot-bubble);
            border: 1px solid var(--card-border);
            color: #e2e8f0;
            border-bottom-left-radius: 4px;
        }
        .bot-message .tier-badge {
            display: inline-block;
            font-size: 0.7rem;
            color: #a78bfa;
            margin-bottom: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .input-area {
            padding: 18px 24px;
            border-top: 1px solid var(--card-border);
            display: flex;
            gap: 12px;
            background: rgba(15, 23, 42, 0.6);
        }
        .input-field {
            flex: 1;
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 12px 18px;
            color: #fff;
            font-size: 0.95rem;
            outline: none;
            transition: all 0.2s;
        }
        .input-field:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2);
        }
        .send-btn {
            background: linear-gradient(135deg, #8b5cf6, #3b82f6);
            border: none;
            color: white;
            padding: 12px 24px;
            border-radius: 14px;
            font-weight: 600;
            font-size: 0.95rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        .send-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 14px rgba(139, 92, 246, 0.4);
        }
        .send-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-title">
                ✨ Shinzo 1.0
                <span class="status-badge"><span class="status-dot"></span> Online</span>
            </div>
            <a href="/docs" target="_blank" class="docs-link">Interactive Swagger API ↗</a>
        </div>
        <div class="chat-box" id="chatBox">
            <div class="message bot-message">
                <div class="tier-badge">Shinzo Companion</div>
                Hey! I'm Shinzo, your emotional companion. I'm here to listen, support, and talk about whatever is on your mind. How's your day going?
            </div>
        </div>
        <div class="input-area">
            <input type="text" id="userInput" class="input-field" placeholder="Share what's on your mind..." autocomplete="off" onkeypress="handleKey(event)">
            <button id="sendBtn" class="send-btn" onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        const chatBox = document.getElementById('chatBox');
        const userInput = document.getElementById('userInput');
        const sendBtn = document.getElementById('sendBtn');
        const userId = 'user-' + Math.random().toString(36).substr(2, 9);
        const conversationId = 'conv-' + Math.random().toString(36).substr(2, 9);

        function handleKey(e) {
            if (e.key === 'Enter') sendMessage();
        }

        async function sendMessage() {
            const text = userInput.value.trim();
            if (!text) return;

            // Append User Message
            const userDiv = document.createElement('div');
            userDiv.className = 'message user-message';
            userDiv.textContent = text;
            chatBox.appendChild(userDiv);
            userInput.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            // Loading state
            userInput.disabled = true;
            sendBtn.disabled = true;

            try {
                const res = await fetch('/v1/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: userId,
                        conversation_id: conversationId,
                        message: text
                    })
                });
                const data = await res.json();
                
                const botDiv = document.createElement('div');
                botDiv.className = 'message bot-message';
                botDiv.innerHTML = `<div class="tier-badge">${data.risk_tier ? 'Risk: ' + data.risk_tier : 'Shinzo'}</div>` + (data.reply || '...');
                chatBox.appendChild(botDiv);
            } catch (err) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'message bot-message';
                errorDiv.textContent = "Sorry, I had trouble connecting: " + err.message;
                chatBox.appendChild(errorDiv);
            } finally {
                userInput.disabled = false;
                sendBtn.disabled = false;
                userInput.focus();
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        }
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)


