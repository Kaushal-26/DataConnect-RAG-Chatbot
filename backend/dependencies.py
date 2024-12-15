from typing import Annotated, Optional

from dotenv import load_dotenv
from fastapi import Depends, HTTPException

from config import settings
from rag import RAGEngine
from repositories import RedisRepository
from services import AirtableService, AIService, HubspotService, NotionService

load_dotenv()


# Redis Repository Dependency
async def get_redis_client():
    try:
        redis_client = RedisRepository(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
        yield redis_client
    finally:
        await redis_client.close()


RedisRepositoryDependency = Annotated[RedisRepository, Depends(get_redis_client)]


# RAG Dependency
async def get_rag_engine():
    try:
        yield RAGEngine()
    except Exception as e:
        print(f"---------- Failed to initialize RAG engine. Please add OPENAI_API_KEY in .env file: {e} ----------")
        yield None  # Return None if RAG engine is not initialized


RAGDependency = Annotated[Optional[RAGEngine], Depends(get_rag_engine)]


# Airtable Service Dependency
async def get_airtable_service(redis_client: RedisRepositoryDependency, rag_engine: RAGDependency):
    try:
        yield AirtableService(
            redis_repository=redis_client,
            authorization_url=f"{settings.AIRTABLE_OAUTH_URL}/authorize",
            client_id=settings.AIRTABLE_CLIENT_ID,
            client_secret=settings.AIRTABLE_CLIENT_SECRET,
            redirect_uri=settings.AIRTABLE_REDIRECT_URI,
            scopes=settings.AIRTABLE_SCOPES,
            rag_engine=rag_engine,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get airtable integration service: {e}")


AirtableServiceDependency = Annotated[AirtableService, Depends(get_airtable_service)]


# Hubspot Service Dependency
async def get_hubspot_service(redis_client: RedisRepositoryDependency, rag_engine: RAGDependency):
    try:
        yield HubspotService(
            redis_repository=redis_client,
            authorization_url=f"{settings.HUBSPOT_OAUTH_URL}/authorize",
            client_id=settings.HUBSPOT_CLIENT_ID,
            client_secret=settings.HUBSPOT_CLIENT_SECRET,
            redirect_uri=settings.HUBSPOT_REDIRECT_URI,
            scopes=settings.HUBSPOT_SCOPES,
            rag_engine=rag_engine,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get hubspot integration service: {e}")


HubspotServiceDependency = Annotated[HubspotService, Depends(get_hubspot_service)]


# Notion Service Dependency
async def get_notion_service(redis_client: RedisRepositoryDependency, rag_engine: RAGDependency):
    try:
        yield NotionService(
            redis_repository=redis_client,
            authorization_url=f"{settings.NOTION_OAUTH_URL}/authorize",
            client_id=settings.NOTION_CLIENT_ID,
            client_secret=settings.NOTION_CLIENT_SECRET,
            redirect_uri=settings.NOTION_REDIRECT_URI,
            rag_engine=rag_engine,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get notion integration service: {e}")


NotionServiceDependency = Annotated[NotionService, Depends(get_notion_service)]


# AI Service Dependency
async def get_ai_service(rag_engine: RAGDependency):
    try:
        # Ensure that the RAG engine is initialized
        assert rag_engine is not None

        yield AIService(rag_engine=rag_engine)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get ai service: {e}")


AIServiceDependency = Annotated[AIService, Depends(get_ai_service)]


__all__ = [
    "AirtableServiceDependency",
    "HubspotServiceDependency",
    "NotionServiceDependency",
    "RedisRepositoryDependency",
]
