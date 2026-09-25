from functools import lru_cache

from langchain_groq import ChatGroq

from src.config import get_settings


@lru_cache
def get_llm() -> ChatGroq:
    settings = get_settings()
    settings.require_keys()
    return ChatGroq(
        model=settings.model,
        temperature=settings.temperature,
        api_key=settings.groq_api_key,
    )
