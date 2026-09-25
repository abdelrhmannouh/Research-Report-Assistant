from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


class MissingConfigError(RuntimeError):
    """Raised when required settings (API keys) are not configured."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    groq_api_key: str = ""
    tavily_api_key: str = ""

    # gpt-oss-20b frequently emits malformed JSON for tool call arguments on
    # Groq (groq.BadRequestError: "tool_use_failed"); gpt-oss-120b is reliable.
    model: str = "openai/gpt-oss-120b"
    temperature: float = 0.0

    max_search_results: int = 3
    max_attempts: int = 3
    retry_backoff_seconds: float = 1.0
    recursion_limit: int = 10

    # When set, the Streamlit app talks to the FastAPI backend at this URL
    # instead of running the pipeline in-process.
    api_url: str = ""

    def require_keys(self) -> None:
        missing = [
            name
            for name, value in (
                ("GROQ_API_KEY", self.groq_api_key),
                ("TAVILY_API_KEY", self.tavily_api_key),
            )
            if not value.strip()
        ]
        if missing:
            raise MissingConfigError(
                f"{', '.join(missing)} {'is' if len(missing) == 1 else 'are'} missing "
                "— add {} to your .env file.".format("it" if len(missing) == 1 else "them")
            )


@lru_cache
def get_settings() -> Settings:
    # Also export .env into os.environ so libraries that read it directly
    # (e.g. LangSmith tracing) pick it up.
    load_dotenv()
    return Settings()
