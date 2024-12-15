# DataConnect: OAuth-powered Multi-SaaS RAG Chatbot

A seamless integration platform that authenticates with **HubSpot**, **Airtable**, and **Notion** via OAuth, extracts valuable data, and transforms it into an intelligent RAG-based chat interface. Query your business data naturally across multiple SaaS tools through a single conversational AI experience.

## Backend

### Requirements

- Python 3.10+
- Dependencies managed with [uv](https://docs.astral.sh/uv/) or use `pip install -r requirements.txt`
    - Install from https://docs.astral.sh/uv/getting-started/installation/

### Setup

- Go to the backend directory
    ```bash
    $ cd backend
    ```
- Run
    ```bash
    $ uv sync
    # or
    $ pip install -r requirements.txt
    ```
- Add `CLIENT_ID` and `CLIENT_SECRET` of different integration to `.env` same as `.env.example`
- Run the server
    ```bash
    $ uv run uvicorn main:app --reload
    # or
    $ uvicorn main:app --reload
    ```
- Signin to `HubSpot`, `Notion` and `Airtable` for oauth2 authentication and load the data.
- After loading the data from integrations, If added `OPENAI_API_KEY` in `.env` file, then you can use the [RAG engine](#use-rag-with-ai-service)

## Frontend

- Go to the frontend directory
    ```bash
    $ cd frontend
    ```
- Install dependencies
    ```bash
    $ npm install
    ```
- Run the frontend
    ```bash
    $ npm run start
    ```
- After loading the data from integrated tools, Chat with the [loaded data](#use-rag-with-ai-service) in frontend, which is powered by [chatbotify](https://react-chatbotify.com/)

## Redis

- We need to have a redis server running on the same machine as the backend.
- Install redis from https://redis.io/docs/install/
    ```bash
    $ redis-server
    ```

## Use RAG with AI Service

- Set `OPENAI_API_KEY` in `.env`.
- Configure openai models as required in `backend/config.py` or use default values.
- Call `/chat` endpoint with **user_id**, **org_id**, **chat_session_id** and **message** to get the response.
    ```bash
    $ curl -X 'POST' \
    'http://127.0.0.1:8000/chat' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    -d 'user_id=1&org_id=1&chat_session_id=1&message=Hi'
    ```

## Development

- Install pre-commit hooks
    ```bash
    $ uv run pre-commit install
    # or
    $ pre-commit install
    ```
- Run pre-commit hooks
    ```bash
    $ uv run pre-commit run --all-files
    # or
    $ pre-commit run --all-files
    ```
