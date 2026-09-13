from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from ddgs import DDGS
from langchain_core.tools import tool

from config import settings


logger = logging.getLogger("cineresearch.tools")


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

def _log_tool_start(tool_name: str, argument: str) -> None:
    logger.info("TOOL START | %s | %s", tool_name, argument)


def _log_tool_success(tool_name: str) -> None:
    logger.info("TOOL COMPLETE | %s", tool_name)


def _log_tool_error(tool_name: str, error: Exception) -> None:
    logger.error(
        "TOOL ERROR | %s | %s",
        tool_name,
        error,
    )


# ---------------------------------------------------------------------------
# Search helper
# ---------------------------------------------------------------------------

def _search_web(
    query: str,
    max_results: int | None = None,
) -> list[dict[str, Any]]:
    """Perform a DuckDuckGo text search."""

    limit = max_results or settings.search_max_results

    with DDGS(timeout=15) as search_client:
        results = search_client.text(
            query,
            max_results=limit,
        )

    return list(results or [])


def _format_search_results(
    results: list[dict[str, Any]],
) -> str:
    """Convert raw search results into compact evidence for the LLM."""

    if not results:
        return "No search results were returned."

    formatted: list[str] = []

    for index, result in enumerate(results, start=1):
        title = result.get("title", "Untitled")
        url = result.get("href", "")
        snippet = result.get("body", "")

        formatted.append(
            f"[{index}] {title}\n"
            f"URL: {url}\n"
            f"Snippet: {snippet}"
        )

    return "\n\n".join(formatted)


# ---------------------------------------------------------------------------
# Movie metadata
# ---------------------------------------------------------------------------

@tool
def movie_search_tool(title: str) -> str:
    """Search the web for authoritative basic metadata about a movie.

    Use this tool when you need the movie's release year, director, cast,
    genres, runtime, synopsis, or other basic metadata.
    """

    _log_tool_start("movie_search_tool", title)

    try:
        query = (
            f'"{title}" movie director cast release year '
            f'genre synopsis'
        )

        results = _search_web(query)

        evidence = _format_search_results(results)

        output = (
            f"MOVIE METADATA SEARCH: {title}\n\n"
            f"{evidence}"
        )

        _log_tool_success("movie_search_tool")

        return output

    except Exception as exc:
        _log_tool_error("movie_search_tool", exc)

        return (
            f"Movie metadata search failed for '{title}'. "
            f"Reason: {exc}"
        )


# ---------------------------------------------------------------------------
# Reviews / critical reception
# ---------------------------------------------------------------------------

@tool
def review_search_tool(title: str) -> str:
    """Research critical reception, reviews, and audience response.

    Use this tool when the user asks whether a movie was well received,
    critically acclaimed, controversial, divisive, or commercially notable.
    """

    _log_tool_start("review_search_tool", title)

    try:
        queries = [
            f'"{title}" film reviews critics reception',
            f'"{title}" Rotten Tomatoes Metacritic reviews',
            f'"{title}" critical reception audience response',
        ]

        collected: list[dict[str, Any]] = []

        for query in queries:
            collected.extend(
                _search_web(
                    query,
                    max_results=3,
                )
            )

        # Remove duplicate URLs.
        unique_results: dict[str, dict[str, Any]] = {}

        for result in collected:
            url = result.get("href", "")
            if url:
                unique_results[url] = result

        evidence = _format_search_results(
            list(unique_results.values())[: settings.search_max_results * 2]
        )

        output = (
            f"CRITICAL RECEPTION RESEARCH: {title}\n\n"
            f"{evidence}"
        )

        _log_tool_success("review_search_tool")

        return output

    except Exception as exc:
        _log_tool_error("review_search_tool", exc)

        return (
            f"Review research failed for '{title}'. "
            f"Reason: {exc}"
        )


# ---------------------------------------------------------------------------
# General web research
# ---------------------------------------------------------------------------

@tool
def web_search_tool(query: str) -> str:
    """Perform live web research for a specific movie-related question.

    Use this for deep-dive questions that basic movie metadata cannot answer,
    such as filmmaking techniques, historical context, production decisions,
    cinematography, controversies, interviews, or award history.
    """

    _log_tool_start("web_search_tool", query)

    try:
        results = _search_web(query)

        evidence = _format_search_results(results)

        output = (
            f"WEB RESEARCH QUERY: {query}\n\n"
            f"{evidence}"
        )

        _log_tool_success("web_search_tool")

        return output

    except Exception as exc:
        _log_tool_error("web_search_tool", exc)

        return (
            f"Web search failed for '{query}'. "
            f"Reason: {exc}"
        )


# ---------------------------------------------------------------------------
# Similar movies
# ---------------------------------------------------------------------------

@tool
def similar_movies_tool(title: str) -> str:
    """Find movies similar to the requested movie.

    Similarity is based on genre, themes, director, cast, style,
    subject matter, or commonly associated recommendations.
    """

    _log_tool_start("similar_movies_tool", title)

    try:
        query = (
            f'"{title}" similar movies films recommendations '
            f'genre themes'
        )

        results = _search_web(
            query,
            max_results=settings.search_max_results,
        )

        evidence = _format_search_results(results)

        output = (
            f"SIMILAR MOVIE RESEARCH: {title}\n\n"
            f"{evidence}"
        )

        _log_tool_success("similar_movies_tool")

        return output

    except Exception as exc:
        _log_tool_error("similar_movies_tool", exc)

        return (
            f"Similar movie research failed for '{title}'. "
            f"Reason: {exc}"
        )


# ---------------------------------------------------------------------------
# Report persistence
# ---------------------------------------------------------------------------

def _safe_filename(title: str) -> str:
    """Convert a movie title into a filesystem-safe filename."""

    normalized = title.strip().lower()

    normalized = re.sub(
        r"[^a-z0-9]+",
        "-",
        normalized,
    )

    normalized = normalized.strip("-")

    return normalized or "movie-report"


@tool
def save_report_tool(
    title: str,
    markdown_content: str,
) -> str:
    """Save a completed movie research report as Markdown.

    The report is stored under the configured reports directory.
    """

    _log_tool_start("save_report_tool", title)

    try:
        reports_path = Path(settings.reports_directory)

        reports_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        filename = f"{_safe_filename(title)}.md"

        output_path = reports_path / filename

        output_path.write_text(
            markdown_content,
            encoding="utf-8",
        )

        _log_tool_success("save_report_tool")

        return (
            f"Report saved successfully: {output_path}"
        )

    except OSError as exc:
        _log_tool_error("save_report_tool", exc)

        return (
            f"Failed to save report for '{title}': {exc}"
        )


# ---------------------------------------------------------------------------
# Public tool registry
# ---------------------------------------------------------------------------

RESEARCH_TOOLS = [
    movie_search_tool,
    review_search_tool,
    web_search_tool,
    similar_movies_tool,
]