"""Configuration layer: loads the env file and builds the OpenAI chat and embedding clients.

Values are never printed or returned by check_env(); only variable names are reported.
"""
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from src.paths import ENV_PATH

load_dotenv(ENV_PATH)

# Must be set for the system to work.
REQUIRED_KEYS = ["CHAT_MODEL_NAME", "OPENAI_API_KEY", "EMBEDDING_MODEL_NAME"]
# Custom base URL; leave empty to use the default OpenAI endpoint.
OPTIONAL_KEYS = ["MODEL_ENDPOINT"]


def check_env() -> dict:
    """Return {name: True/False} for every variable. Never returns a value."""
    return {key: bool(os.getenv(key)) for key in REQUIRED_KEYS + OPTIONAL_KEYS}


def _require() -> None:
    missing = [key for key in REQUIRED_KEYS if not os.getenv(key)]
    if missing:
        raise RuntimeError(
            "Missing environment variables: " + ", ".join(missing)
            + ". Please fill them in your env file."
        )


def get_llm() -> ChatOpenAI:
    _require()
    return ChatOpenAI(
        model=os.getenv("CHAT_MODEL_NAME"),
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("MODEL_ENDPOINT") or None,
        temperature=0,
    )


def get_embeddings() -> OpenAIEmbeddings:
    _require()
    return OpenAIEmbeddings(
        model=os.getenv("EMBEDDING_MODEL_NAME"),
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("MODEL_ENDPOINT") or None,
    )
