from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, HTTPException

from config import settings
from repository import RedisRepository
from services import AirtableService, HubspotService, NotionService

load_dotenv()


# Redis Repository Dependency
async def get_redis_client():
    try:
        redis_client = RedisRepository(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
        yield redis_client
    finally:
        await redis_client.close()


RedisRepositoryDependency = Annotated[RedisRepository, Depends(get_redis_client)]


# Airtable Service Dependency
async def get_airtable_service(redis_client: RedisRepositoryDependency):
    try:
        yield AirtableService(
            redis_client=redis_client,
            authorization_url=f"{settings.AIRTABLE_OAUTH_URL}/authorize",
            client_id=settings.AIRTABLE_CLIENT_ID,
            client_secret=settings.AIRTABLE_CLIENT_SECRET,
            redirect_uri=settings.AIRTABLE_REDIRECT_URI,
            scopes=settings.AIRTABLE_SCOPES,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get airtable integration service: {e}")


AirtableServiceDependency = Annotated[AirtableService, Depends(get_airtable_service)]


# Hubspot Service Dependency
async def get_hubspot_service(redis_client: RedisRepositoryDependency):
    try:
        yield HubspotService(
            redis_client=redis_client,
            authorization_url=f"{settings.HUBSPOT_OAUTH_URL}/authorize",
            client_id=settings.HUBSPOT_CLIENT_ID,
            client_secret=settings.HUBSPOT_CLIENT_SECRET,
            redirect_uri=settings.HUBSPOT_REDIRECT_URI,
            scopes=settings.HUBSPOT_SCOPES,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get hubspot integration service: {e}")


HubspotServiceDependency = Annotated[HubspotService, Depends(get_hubspot_service)]


# Notion Service Dependency
async def get_notion_service(redis_client: RedisRepositoryDependency):
    try:
        yield NotionService(
            redis_client=redis_client,
            authorization_url=f"{settings.NOTION_OAUTH_URL}/authorize",
            client_id=settings.NOTION_CLIENT_ID,
            client_secret=settings.NOTION_CLIENT_SECRET,
            redirect_uri=settings.NOTION_REDIRECT_URI,
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
