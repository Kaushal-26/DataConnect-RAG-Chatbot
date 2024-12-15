import base64
from abc import ABC, abstractmethod
from typing import Any, List, Optional

from fastapi import Request
from fastapi.responses import HTMLResponse

from rag import RAGEngine
from repositories.redis import RedisRepository
from schemas import IntegrationItem


class BaseIntegrationService(ABC):
    """Base integration service class"""

    def __init__(
        self,
        redis_repository: RedisRepository,
        authorization_url: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes: Optional[str] = None,
        rag_engine: Optional[RAGEngine] = None,
    ):
        # Initialize the client id and secret
        self.client_id = client_id
        self.client_secret = client_secret

        # Initialize the redirect uri and scope
        self.redirect_uri = redirect_uri
        self.scopes = scopes

        # Initialize the authorization url
        self.authorization_url = (
            f"{authorization_url}"
            f"?client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type=code"
            f"&owner=user"
            f"{f'&scope={scopes}' if scopes else ''}"
        )

        # Initialize the encoded client id and secret
        self.encoded_client_id_secret = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

        # Initialize the redis client
        self.redis_repository = redis_repository

        # Initialize the RAG engine
        self.rag_engine = rag_engine

    @abstractmethod
    async def authorize(self, user_id: str, org_id: str) -> str:
        pass

    @abstractmethod
    async def oauth2callback(self, request: Request) -> HTMLResponse:
        pass

    @abstractmethod
    async def get_credentials(self, user_id: str, org_id: str) -> Any:
        pass

    @abstractmethod
    async def get_items(self, user_id: str, org_id: str) -> List[IntegrationItem]:
        pass

    async def add_integration_items_to_rag(self, user_id: str, org_id: str, items_json: str, integration_type: str):
        """Add the items to the RAG engine"""
        if self.rag_engine is None:
            return

        metadata = {"integration_type": integration_type}

        await self.rag_engine.add_data(user_id=user_id, org_id=org_id, data=items_json, metadata=metadata)
