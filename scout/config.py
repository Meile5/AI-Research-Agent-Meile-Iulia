"""Settings from .env and the Groq model used by the agent."""
import os

from dotenv import load_dotenv
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.profiles.openai import OpenAIModelProfile
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

load_dotenv()

OPENALEX_API_KEY = os.getenv("OPENALEX_API_KEY") or None


def build_model() -> OpenAIChatModel:
    """Build the LLM. Called only when we really talk to Groq, so tests work without a key."""
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise RuntimeError("LLM_API_KEY is missing. Put it in your .env file.")

    provider = OpenAIProvider(
        base_url=os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
        api_key=api_key,
    )
    return OpenAIChatModel(
        os.getenv("LLM_MODEL", "openai/gpt-oss-120b"),
        provider=provider,
        # Groq refuses JSON mode together with tools, so PromptedOutput must not turn it on
        profile=OpenAIModelProfile(supports_json_object_output=False),
        settings=ModelSettings(max_tokens=800, temperature=0),
    )