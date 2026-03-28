"""Factory for the OpenAI LLM client."""

from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_openai import ChatOpenAI

if TYPE_CHECKING:
    from app.config import Settings


def create_llm_client(settings: Settings) -> ChatOpenAI:
    """Instantiate and return a configured ``ChatOpenAI`` client.

    Parameters
    ----------
    settings : Settings
        Application settings containing the API key, model name,
        and temperature.

    Returns
    -------
    ChatOpenAI
        A ready-to-use LangChain chat model instance.
    """
    return ChatOpenAI(
        api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_MODEL,
        temperature=settings.OPENAI_TEMPERATURE,
    )
