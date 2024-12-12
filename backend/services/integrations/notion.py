import asyncio
import base64
import json
import secrets
from typing import Any, List

import httpx
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse

from config import settings
from schemas import IntegrationItem
from utils import print_items

from .base import BaseIntegrationService


class NotionService(BaseIntegrationService):
    """Notion integration service inherits from BaseIntegrationService"""

    async def authorize(self, user_id: str, org_id: str) -> str:
        """Authorize the user to access the Notion API"""

        state_data = {
            "state": secrets.token_urlsafe(32),
            "user_id": user_id,
            "org_id": org_id,
        }
        # Make sure the state data is encoded in a way that is safe to use as a URL parameter
        encoded_state = base64.urlsafe_b64encode(json.dumps(state_data).encode("utf-8")).decode("utf-8")

        auth_url = f"{self.authorization_url}&state={encoded_state}"
        await self.redis_client.add(f"notion_state:{org_id}:{user_id}", json.dumps(state_data), expire=600)

        return auth_url

    async def oauth2callback(self, request: Request) -> str:
        """Callback for the OAuth2 flow"""

        if request.query_params.get("error"):
            raise HTTPException(status_code=400, detail=request.query_params.get("error"))

        code = request.query_params.get("code")
        encoded_state = request.query_params.get("state")
        # Decode the state data
        state_data = json.loads(base64.urlsafe_b64decode(encoded_state).decode("utf-8"))

        original_state = state_data.get("state")
        user_id = state_data.get("user_id")
        org_id = state_data.get("org_id")

        saved_state = await self.redis_client.get(f"notion_state:{org_id}:{user_id}")

        if not saved_state or original_state != json.loads(saved_state).get("state"):
            raise HTTPException(status_code=400, detail="State does not match.")

        async with httpx.AsyncClient() as client:
            response, _ = await asyncio.gather(
                client.post(
                    f"{settings.NOTION_OAUTH_URL}/token",
                    json={"grant_type": "authorization_code", "code": code, "redirect_uri": self.redirect_uri},
                    headers={
                        "Authorization": f"Basic {self.encoded_client_id_secret}",
                        "Content-Type": "application/json",
                    },
                ),
                self.redis_client.delete(f"notion_state:{org_id}:{user_id}"),
            )

        await self.redis_client.add(f"notion_credentials:{org_id}:{user_id}", json.dumps(response.json()), expire=600)

        close_window_script = """
        <html>
            <script>
                window.close();
            </script>
        </html>
        """
        return HTMLResponse(content=close_window_script)

    async def get_credentials(self, user_id: str, org_id: str) -> dict:
        """Get the credentials for the Notion API"""

        credentials = await self.redis_client.get(f"notion_credentials:{org_id}:{user_id}")
        if not credentials:
            raise HTTPException(status_code=400, detail="No credentials found.")

        credentials = json.loads(credentials)
        if not credentials:
            raise HTTPException(status_code=400, detail="No credentials found.")

        await self.redis_client.delete(f"notion_credentials:{org_id}:{user_id}")

        return credentials

    async def get_items(self, credentials: str) -> List[IntegrationItem]:
        """Aggregates all metadata relevant for a notion integration"""

        credentials = json.loads(credentials)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.NOTION_API_URL}/search",
                headers={
                    "Authorization": f"Bearer {credentials.get('access_token')}",
                    "Notion-Version": settings.NOTION_VERSION,
                },
            )
            response.raise_for_status()

        if response.status_code == 200:
            results = response.json()["results"]

            # Create a list of tasks to create the integration item metadata objects
            task_integration_item_metadata = [
                self._create_integration_item_metadata_object(result) for result in results
            ]
            # Run the tasks in parallel and wait for them to complete
            list_of_integration_item_metadata = await asyncio.gather(*task_integration_item_metadata)

        print_items(
            items=[item.model_dump(mode="json") for item in list_of_integration_item_metadata],
            message="Notion Integration Items",
        )

        return list_of_integration_item_metadata

    async def _create_integration_item_metadata_object(self, response_json: dict) -> IntegrationItem:
        """Creates an integration metadata object from the response"""

        name = self._recursive_dict_search(response_json["properties"], "content")

        parent_type = "" if response_json["parent"]["type"] is None else response_json["parent"]["type"]
        parent_id = None if response_json["parent"]["type"] == "workspace" else response_json["parent"][parent_type]

        name = self._recursive_dict_search(response_json, "content") if name is None else name
        name = "multi_select" if name is None else name
        name = response_json["object"] + " " + name

        integration_item_metadata = IntegrationItem(
            id=response_json["id"],
            type=response_json["object"],
            name=name,
            creation_time=response_json["created_time"],
            last_modified_time=response_json["last_edited_time"],
            parent_id=parent_id,
        )

        return integration_item_metadata

    def _recursive_dict_search(self, data: Any, target_key: str) -> Any:
        """Recursively search for a key in a dictionary of dictionaries."""

        if target_key in data:
            return data[target_key]

        for value in data.values():
            if isinstance(value, dict):
                result = self._recursive_dict_search(value, target_key)
                if result is not None:
                    return result
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        result = self._recursive_dict_search(item, target_key)
                        if result is not None:
                            return result

        return None
