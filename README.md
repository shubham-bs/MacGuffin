# 🎬 CineResearch

### Autonomous AI Movie Research Agent

CineResearch is a Python-based AI research agent that autonomously investigates
movies using specialized domain tools, dynamically selecting the tools required
to answer a user's research request.

Unlike a conventional LLM wrapper that sends one prompt and returns one response,
CineResearch implements an agentic tool-use loop:

```text
┌──────────────────────────────────────────────────────────────┐
│                         USER                                 │
│                                                              │
│ "Research Interstellar. Tell me about its cast, reception,  │
│  awards, director and similar movies."                      │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                    CINE RESEARCH AGENT                       │
│                                                              │
│       LLM + Tool Calling + Agent Execution Loop              │
│                                                              │
│      Dynamically determines which tools are required         │
└────────────────────────────┬─────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
       ┌────────────┐ ┌────────────┐ ┌──────────────┐
       │   Movie    │ │  Reviews   │ │    Web       │
       │   Search   │ │  Research  │ │   Research   │
       └────────────┘ └────────────┘ └──────────────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Evidence         │
                    │ Aggregation      │
                    └────────┬─────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                 STRUCTURED OUTPUT                            │
│                                                              │
│                    MovieResearch                              │
│                    (Pydantic)                                │
│                                                              │
│ title • year • director • cast • genres • synopsis           │
│ reception • awards • similar movies • sources • tools       │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Markdown Report  │
                    │ reports/*.md     │
                    └──────────────────┘
