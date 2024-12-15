from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Airtable Integration Credentials
    AIRTABLE_CLIENT_ID: str
    AIRTABLE_CLIENT_SECRET: str
    AIRTABLE_REDIRECT_URI: str = f"{BACKEND_URL}/integrations/airtable/oauth2callback"
    AIRTABLE_SCOPES: str = "data.records:read data.records:write data.recordComments:read data.recordComments:write schema.bases:read schema.bases:write"

    AIRTABLE_API_URL: str = "https://api.airtable.com/v0"
    AIRTABLE_OAUTH_URL: str = "https://airtable.com/oauth2/v1"

    # Hubspot Integration Credentials
    HUBSPOT_CLIENT_ID: str
    HUBSPOT_CLIENT_SECRET: str
    HUBSPOT_REDIRECT_URI: str = f"{BACKEND_URL}/integrations/hubspot/oauth2callback"
    HUBSPOT_SCOPES: str = "crm.objects.contacts.read crm.objects.companies.read"

    HUBSPOT_API_URL: str = "https://api.hubapi.com"
    HUBSPOT_OAUTH_URL: str = "https://app.hubspot.com/oauth"

    # Notion Integration Credentials
    NOTION_CLIENT_ID: str
    NOTION_CLIENT_SECRET: str
    NOTION_REDIRECT_URI: str = f"{BACKEND_URL}/integrations/notion/oauth2callback"
    NOTION_SCOPES: Optional[str] = None

    NOTION_API_URL: str = "https://api.notion.com/v1"
    NOTION_OAUTH_URL: str = f"{NOTION_API_URL}/oauth"

    NOTION_VERSION: str = "2022-06-28"

    # RAG
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-large"
    OPENAI_MODEL: str = "gpt-4o"
    CHAT_MEMORY_TOKEN_LIMIT: int = 5000

    RAG_STORAGE_PATH: str = "./rag_storage"


settings = Settings()
