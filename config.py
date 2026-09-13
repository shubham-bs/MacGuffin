from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Application configuration loaded from environment variables."""

    llm_api_key: str
    llm_model: str
    llm_base_url: str | None
    temperature: float
    request_timeout: float
    max_agent_iterations: int
    search_max_results: int
    reports_directory: str

    @classmethod
    def from_environment(cls) -> "Settings":
        """Build application settings from environment variables."""

        api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY", "")

        model = os.getenv(
            "LLM_MODEL",
            "gpt-4o-mini",
        )

        base_url = os.getenv("LLM_BASE_URL")

        temperature = float(
            os.getenv("LLM_TEMPERATURE", "0")
        )

        request_timeout = float(
            os.getenv("LLM_REQUEST_TIMEOUT", "45")
        )

        max_agent_iterations = int(
            os.getenv("MAX_AGENT_ITERATIONS", "8")
        )

        search_max_results = int(
            os.getenv("SEARCH_MAX_RESULTS", "5")
        )

        reports_directory = os.getenv(
            "REPORTS_DIRECTORY",
            "reports",
        )

        if not api_key:
            raise ValueError(
                "Missing LLM API key. Set LLM_API_KEY or OPENAI_API_KEY "
                "in your .env file."
            )

        if not 0 <= temperature <= 2:
            raise ValueError(
                "LLM_TEMPERATURE must be between 0 and 2."
            )

        if max_agent_iterations < 1:
            raise ValueError(
                "MAX_AGENT_ITERATIONS must be at least 1."
            )

        if search_max_results < 1:
            raise ValueError(
                "SEARCH_MAX_RESULTS must be at least 1."
            )

        return cls(
            llm_api_key=api_key,
            llm_model=model,
            llm_base_url=base_url,
            temperature=temperature,
            request_timeout=request_timeout,
            max_agent_iterations=max_agent_iterations,
            search_max_results=search_max_results,
            reports_directory=reports_directory,
        )


settings = Settings.from_environment()