from __future__ import annotations

import logging

from fastapi import FastAPI

from apps.api.routes.catalog import router as catalog_router
from apps.api.routes.chat import router as chat_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")

app = FastAPI(title="Backend-first Chatbot Service")
app.include_router(catalog_router)
app.include_router(chat_router)
