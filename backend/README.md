# DataConnect: OAuth-powered Multi-SaaS RAG Chatbot

A seamless integration platform that authenticates with **HubSpot**, **Airtable**, and **Notion** via OAuth, extracts valuable data, and transforms it into an intelligent RAG-based chat interface. Query your business data naturally across multiple SaaS tools through a single conversational AI experience.

## Backend

### Requirements

- Python 3.10+
- Dependencies managed with [uv](https://docs.astral.sh/uv/).
    - Install from https://docs.astral.sh/uv/getting-started/installation/

### Setup

- Run
    ```bash
    uv sync
    ```
- Add `CLIENT_ID` and `CLIENT_SECRET` of different integration to `.env` same as `.env.example`
- Run the server
    ```bash
    uv run uvicorn main:app --reload
    ```


# Development

- Install pre-commit hooks
    ```bash
    uv run pre-commit install
    ```
- Run pre-commit hooks
    ```bash
    uv run pre-commit run --all-files
    ```
