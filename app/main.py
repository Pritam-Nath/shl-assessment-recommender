from fastapi import FastAPI

from app.models import ChatRequest, ChatResponse
from app.recommender import SHLAgent

app = FastAPI(title="Conversational SHL Assessment Recommender")
agent = SHLAgent()


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "Conversational SHL Assessment Recommender",
        "status": "ok",
        "health": "/health",
        "chat": "/chat",
        "docs": "/docs",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return agent.respond(request.messages)
