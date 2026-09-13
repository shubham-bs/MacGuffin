from __future__ import annotations

import logging
from typing import Any

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from config import settings
from models import MovieResearch
from tools import RESEARCH_TOOLS


logger = logging.getLogger("cineresearch.agent")


# ---------------------------------------------------------------------------
# Agent instructions
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
You are CineResearch, an autonomous AI movie research agent.

Your job is to research movies using the available domain-specific tools
and gather accurate, evidence-based information.

OPERATING RULES
---------------

1. Identify the primary movie being researched from the user's request.

2. Dynamically choose the tools required to answer the request.
   Do NOT call every tool automatically.

3. Use movie_search_tool for:
   - title
   - release year
   - director
   - genres
   - principal cast
   - synopsis

4. Use review_search_tool for:
   - critical reception
   - audience reception
   - review consensus
   - critical controversy

5. Use similar_movies_tool when the user asks for:
   - similar movies
   - recommendations
   - movies with similar themes/style/genre

6. Use web_search_tool for deeper questions such as:
   - filmmaking techniques
   - production decisions
   - historical context
   - awards
   - controversies
   - interviews
   - cinematography
   - unusual facts

7. You may call multiple tools sequentially when necessary.

8. Do not fabricate facts.
   If evidence is unavailable, explicitly state that the information
   could not be verified rather than inventing it.

9. Prefer primary or authoritative sources when search results provide them.

10. Gather and synthesize the research returned by the tools.

11. Preserve URLs returned by the research tools so they can be used
    as sources in the final report.

12. Keep the synopsis concise and avoid unnecessary spoilers.

13. Do not expose hidden chain-of-thought or private reasoning.
    Tool execution events are sufficient for observability.

14. Your response should contain the gathered research needed to construct
    a final MovieResearch report.
"""


# ---------------------------------------------------------------------------
# Model construction
# ---------------------------------------------------------------------------

def _build_model() -> ChatOpenAI:
    """Construct the configured chat model."""

    model_kwargs: dict[str, Any] = {
        "model": settings.llm_model,
        "api_key": settings.llm_api_key,
        "temperature": settings.temperature,
        "timeout": settings.request_timeout,
        "max_retries": 2,
    }

    if settings.llm_base_url:
        model_kwargs["base_url"] = settings.llm_base_url

    return ChatOpenAI(**model_kwargs)


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class CineResearchAgent:
    """Autonomous movie research agent."""

    def __init__(self) -> None:
        self.model = _build_model()

        # IMPORTANT:
        # This agent is responsible ONLY for tool selection and research.
        #
        # We intentionally do NOT use ToolStrategy(MovieResearch) here.
        # Groq's structured-output parsing should happen in a separate
        # model call after the tool-calling phase is complete.
        self.agent = create_agent(
            model=self.model,
            tools=RESEARCH_TOOLS,
            system_prompt=SYSTEM_PROMPT,
            name="cine_research_agent",
        )

        # Separate model instance configured for structured output.
        #
        # This model has NO tools attached. It is used only after the
        # research agent has finished gathering information.
        self.structured_model = self.model.with_structured_output(
            MovieResearch
        )

    # -----------------------------------------------------------------------
    # Extract tool calls from agent messages
    # -----------------------------------------------------------------------

    @staticmethod
    def _extract_tool_events(messages: list[Any]) -> list[str]:
        """
        Extract actual tool names invoked during the agent run.

        The application-side trace is authoritative rather than relying
        on the LLM to report which tools it used.
        """

        tool_events: list[str] = []

        for message in messages:
            tool_calls = getattr(message, "tool_calls", None)

            if not tool_calls:
                continue

            for call in tool_calls:
                tool_name = call.get("name", "unknown_tool")

                if tool_name:
                    tool_events.append(tool_name)

        # Deduplicate while preserving order.
        return list(dict.fromkeys(tool_events))

    # -----------------------------------------------------------------------
    # Convert research messages into text
    # -----------------------------------------------------------------------

    @staticmethod
    def _build_research_context(messages: list[Any]) -> str:
        """
        Convert the agent's conversation/tool results into a compact
        research context for the final structured-output call.
        """

        context_parts: list[str] = []

        for message in messages:
            role = getattr(message, "type", None)

            # We primarily care about tool results and the final agent
            # response. Including all useful textual content gives the
            # structured model enough evidence to synthesize the report.
            content = getattr(message, "content", None)

            if not content:
                continue

            if isinstance(content, list):
                content = "\n".join(
                    str(item)
                    for item in content
                )

            content = str(content).strip()

            if not content:
                continue

            if role == "tool":
                context_parts.append(
                    f"[TOOL RESULT]\n{content}"
                )
            elif role == "ai":
                context_parts.append(
                    f"[AGENT RESEARCH]\n{content}"
                )

        return "\n\n".join(context_parts)

    # -----------------------------------------------------------------------
    # Final structured-output generation
    # -----------------------------------------------------------------------

    def _create_structured_report(
        self,
        user_query: str,
        research_context: str,
        tools_used: list[str],
    ) -> MovieResearch:
        """
        Convert gathered research into the MovieResearch Pydantic schema.

        This is intentionally a separate LLM call from the tool-calling
        agent so structured output and tool use are not combined in the
        same Groq request.
        """

        if not research_context.strip():
            raise RuntimeError(
                "The research agent returned no usable research data."
            )

        prompt = f"""
You are the final report generator for CineResearch.

Create a MovieResearch object using ONLY the research evidence provided
below.

USER REQUEST
------------
{user_query}

TOOLS ACTUALLY USED
-------------------
{", ".join(tools_used) if tools_used else "None"}

RESEARCH EVIDENCE
-----------------
{research_context}

REQUIREMENTS
------------

1. Synthesize the evidence rather than blindly copying snippets.

2. Do not invent missing information.

3. If a field cannot be verified from the evidence, use a concise
   indication such as "Not verified from available sources."

4. Keep the synopsis concise and avoid major spoilers.

5. The sources field must contain URLs that actually appear in the
   research evidence.

6. The tools_used field must contain ONLY the tools listed above.

7. Return the final answer according to the MovieResearch schema.
"""

        structured_response = self.structured_model.invoke(prompt)

        if not isinstance(structured_response, MovieResearch):
            raise RuntimeError(
                "Structured model did not return a valid MovieResearch object."
            )

        # The application-side trace is authoritative.
        structured_response.tools_used = tools_used

        return structured_response

    # -----------------------------------------------------------------------
    # Main research pipeline
    # -----------------------------------------------------------------------

    def research(
        self,
        user_query: str,
    ) -> tuple[MovieResearch, list[str]]:
        """
        Run autonomous research followed by structured report generation.

        Returns:
            tuple[MovieResearch, list[str]]
        """

        if not user_query.strip():
            raise ValueError(
                "Research query cannot be empty."
            )

        logger.info(
            "RESEARCH START | query=%s",
            user_query,
        )

        try:
            # ---------------------------------------------------------------
            # PHASE 1
            # Autonomous tool-calling research
            # ---------------------------------------------------------------

            result = self.agent.invoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": user_query,
                        }
                    ]
                },
                config={
                    "recursion_limit": settings.max_agent_iterations * 2 + 1
                },
            )

            messages = result.get("messages", [])

            if not messages:
                raise RuntimeError(
                    "Research agent returned no messages."
                )

            # Determine which tools were ACTUALLY called.
            tool_events = self._extract_tool_events(messages)

            logger.info(
                "RESEARCH TOOLS | query=%s | tools=%s",
                user_query,
                tool_events,
            )

            # ---------------------------------------------------------------
            # Build evidence context
            # ---------------------------------------------------------------

            research_context = self._build_research_context(
                messages
            )

            if not research_context.strip():
                raise RuntimeError(
                    "Research agent completed without returning "
                    "usable research evidence."
                )

            # ---------------------------------------------------------------
            # PHASE 2
            # Structured report generation
            # ---------------------------------------------------------------

            logger.info(
                "STRUCTURED REPORT START | query=%s",
                user_query,
            )

            structured_response = self._create_structured_report(
                user_query=user_query,
                research_context=research_context,
                tools_used=tool_events,
            )

            logger.info(
                "RESEARCH COMPLETE | movie=%s | tools=%s",
                structured_response.title,
                tool_events,
            )

            return structured_response, tool_events

        except Exception:
            logger.exception(
                "RESEARCH FAILED | query=%s",
                user_query,
            )
            raise