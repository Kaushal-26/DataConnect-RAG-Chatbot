import os
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, HTTPException

from repository import RedisRepository
from services import AirtableService, HubspotService, NotionService

load_dotenv()


# Redis Repository Dependency
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", 6379)
REDIS_DB = os.environ.get("REDIS_DB", 0)


async def get_redis_client():
    try:
        redis_client = RedisRepository(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        yield redis_client
    finally:
        await redis_client.close()


RedisRepositoryDependency = Annotated[RedisRepository, Depends(get_redis_client)]

# Airtable Service Dependency
AIRTABLE_CLIENT_ID = os.environ.get("AIRTABLE_CLIENT_ID")
AIRTABLE_CLIENT_SECRET = os.environ.get("AIRTABLE_CLIENT_SECRET")
AIRTABLE_REDIRECT_URI = "http://localhost:8000/integrations/airtable/oauth2callback"
AIRTABLE_AUTHORIZATION_URL = "https://airtable.com/oauth2/v1/authorize"
AIRTABLE_SCOPES = "data.records:read data.records:write data.recordComments:read data.recordComments:write schema.bases:read schema.bases:write"


async def get_airtable_service(redis_client: RedisRepositoryDependency):
    try:
        print(f"AIRTABLE_AUTHORIZATION_URL: {AIRTABLE_AUTHORIZATION_URL}")
        yield AirtableService(
            redis_client=redis_client,
            authorization_url=AIRTABLE_AUTHORIZATION_URL,
            client_id=AIRTABLE_CLIENT_ID,
            client_secret=AIRTABLE_CLIENT_SECRET,
            redirect_uri=AIRTABLE_REDIRECT_URI,
            scopes=AIRTABLE_SCOPES,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get airtable integration service: {e}")


AirtableServiceDependency = Annotated[AirtableService, Depends(get_airtable_service)]

# Hubspot Service Dependency
HUBSPOT_CLIENT_ID = os.environ.get("HUBSPOT_CLIENT_ID")
HUBSPOT_CLIENT_SECRET = os.environ.get("HUBSPOT_CLIENT_SECRET")
HUBSPOT_REDIRECT_URI = "http://localhost:8000/integrations/hubspot/oauth2callback"
HUBSPOT_SCOPES = "crm.objects.contacts.read crm.objects.companies.read"
HUBSPOT_AUTHORIZATION_URL = "https://app.hubspot.com/oauth/authorize"


async def get_hubspot_service(redis_client: RedisRepositoryDependency):
    try:
        yield HubspotService(
            redis_client=redis_client,
            authorization_url=HUBSPOT_AUTHORIZATION_URL,
            client_id=HUBSPOT_CLIENT_ID,
            client_secret=HUBSPOT_CLIENT_SECRET,
            redirect_uri=HUBSPOT_REDIRECT_URI,
            scopes=HUBSPOT_SCOPES,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get hubspot integration service: {e}")


HubspotServiceDependency = Annotated[HubspotService, Depends(get_hubspot_service)]


# Notion Service Dependency
NOTION_CLIENT_ID = os.environ.get("NOTION_CLIENT_ID")
NOTION_CLIENT_SECRET = os.environ.get("NOTION_CLIENT_SECRET")
NOTION_REDIRECT_URI = "http://localhost:8000/integrations/notion/oauth2callback"
NOTION_AUTHORIZATION_URL = "https://api.notion.com/v1/oauth/authorize"


async def get_notion_service(redis_client: RedisRepositoryDependency):
    try:
        yield NotionService(
            redis_client=redis_client,
            authorization_url=NOTION_AUTHORIZATION_URL,
            client_id=NOTION_CLIENT_ID,
            client_secret=NOTION_CLIENT_SECRET,
            redirect_uri=NOTION_REDIRECT_URI,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get notion integration service: {e}")


NotionServiceDependency = Annotated[NotionService, Depends(get_notion_service)]


__all__ = [
    "AirtableServiceDependency",
    "HubspotServiceDependency",
    "NotionServiceDependency",
    "RedisRepositoryDependency",
]
