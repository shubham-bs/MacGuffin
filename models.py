from __future__ import annotations

from pydantic import BaseModel, Field


class MovieResearch(BaseModel):
    """Structured output produced by the CineResearch agent."""

    title: str = Field(description="The canonical movie title.")
    year: int = Field(description="The movie's original release year.")
    director: str = Field(description="The movie's director or directors.")
    genres: list[str] = Field(
        description="Primary genres associated with the movie."
    )
    cast: list[str] = Field(
        description="Important principal cast members."
    )
    synopsis: str = Field(
        description="A concise, spoiler-aware synopsis of the movie."
    )
    critical_reception: str = Field(
        description="A concise synthesis of critical and audience reception."
    )
    awards: list[str] = Field(
        description="Important awards or nominations associated with the movie."
    )
    similar_movies: list[str] = Field(
        description="Movies with similar themes, genre, style, or subject matter."
    )
    sources: list[str] = Field(
        description="URLs or source identifiers used to produce the report."
    )
    tools_used: list[str] = Field(
        description="Names of CineResearch tools actually used during research."
    )