# MacGuffin

### Autonomous Movie Research Agent

MacGuffin is an AI-powered movie research agent that autonomously selects web-search tools, gathers information from multiple sources, and synthesizes the results into a structured movie research report.

## Overview

Instead of relying on a single search query, MacGuffin uses an agentic workflow to decide which research tools are relevant to a movie request.

The system separates **research** from **structured report generation**:

1. The agent receives a movie query.
2. The LLM dynamically selects relevant research tools.
3. Tools retrieve information from the web.
4. Retrieved evidence is consolidated.
5. A separate structured-output LLM call converts the evidence into a validated `MovieResearch` schema.
6. The final report is displayed and saved as Markdown.

## Architecture

```text
                         User
                          │
                          ▼
                  ┌───────────────┐
                  │  Agent LLM    │
                  │   GPT-OSS     │
                  └───────┬───────┘
                          │
                   Dynamic Tool
                     Selection
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
   Movie Search     Review Search    Web Search
          │               │               │
          └───────────────┼───────────────┘
                          │
                          ▼
                  Research Evidence
                          │
                          ▼
                  ┌───────────────┐
                  │ Structured    │
                  │ Output LLM    │
                  └───────┬───────┘
                          │
                          ▼
                  MovieResearch
                    (Pydantic)
                          │
                          ▼
                    Markdown Report
```

## Features

- Autonomous tool selection
- Movie metadata research
- Critical and audience reception research
- Similar-movie discovery
- General web research for deeper questions
- Pydantic-validated structured output
- Application-level tool execution tracing
- Markdown report generation
- Configurable LLM endpoint and model
- Environment-based configuration

## Research Tools

| Tool | Purpose |
|---|---|
| `movie_search_tool` | Movie metadata, cast, director, genre, release year and synopsis |
| `review_search_tool` | Critical reception, audience response and review consensus |
| `similar_movies_tool` | Movies with similar themes, genres or styles |
| `web_search_tool` | Awards, production details, filmmaking information and deeper research |
| `save_report_tool` | Persists the final report as Markdown |

The agent does not automatically execute every tool. Tool selection is determined by the LLM based on the research request.

## Structured Output

Research results are validated against the following Pydantic model:

```python
class MovieResearch(BaseModel):
    title: str
    year: int
    director: str
    genres: list[str]
    cast: list[str]
    synopsis: str
    critical_reception: str
    awards: list[str]
    similar_movies: list[str]
    sources: list[str]
    tools_used: list[str]
```

This provides a predictable interface between the research agent and the final report.

## Tech Stack

- **Python**
- **LangChain**
- **LangGraph**
- **Pydantic**
- **OpenAI-compatible LLM API**
- **GPT-OSS 20B**
- **Groq**
- **DDGS**
- **python-dotenv**

## Project Structure

```text
MacGuffin/
├── agent.py
├── config.py
├── main.py
├── models.py
├── tools.py
├── requirements.txt
├── README.md
└── reports/
```

### `agent.py`

Implements the autonomous research workflow, tool selection, research aggregation and structured report generation.

### `tools.py`

Contains the domain-specific research tools and search functionality.

### `models.py`

Defines the Pydantic schema used for validating structured movie research.

### `config.py`

Loads environment variables and application configuration.

### `main.py`

Provides the CLI interface and handles final report display and persistence.

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/shubham-bs/MacGuffin.git
cd MacGuffin
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file:

```env
LLM_API_KEY=your_api_key
LLM_MODEL=openai/gpt-oss-20b
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_TEMPERATURE=0
LLM_REQUEST_TIMEOUT=60
MAX_AGENT_ITERATIONS=8
SEARCH_MAX_RESULTS=5
REPORTS_DIRECTORY=reports
```

### 5. Run

```bash
python main.py
```

Example:

```text
What movie would you like me to research?
> Dune
```

The completed report is saved under:

```text
reports/dune.md
```

## Design Decisions

### Separate research and structured output

MacGuffin intentionally separates tool calling from structured-output generation.

The first LLM call is responsible for deciding which tools to use and gathering evidence. A second LLM call converts that evidence into the `MovieResearch` schema.

This keeps the tool-calling and structured-output stages independent and makes the pipeline easier to validate and extend.

### Application-side tool tracing

The application records tools from actual tool-call messages rather than relying on the LLM to report which tools it used.

This makes `tools_used` an execution trace rather than model-generated metadata.

## Example

A query such as:

```text
Dune
```

can result in the agent selecting:

```text
movie_search_tool
review_search_tool
web_search_tool
similar_movies_tool
```

The collected evidence is then synthesized into a structured movie report containing metadata, reception, awards, similar movies and source URLs.

## License

MIT

