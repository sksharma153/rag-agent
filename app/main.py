from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.documents import router as document_router

app = FastAPI(title="Enterprise RAG Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(chat_router)
app.include_router(document_router)