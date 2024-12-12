import asyncio
import base64
import hashlib
import json
import secrets
from typing import Any, List, Optional

import httpx
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse

from config import settings
from schemas import IntegrationItem
from utils import print_items

from .base import BaseIntegrationService


class AirtableService(BaseIntegrationService):
    """Airtable integration service inherits from BaseIntegrationService"""

    async def authorize(self, user_id: str, org_id: str) -> str:
        """Authorize the user to access the Airtable API"""

        state_data = {
            "state": secrets.token_urlsafe(32),
            "user_id": user_id,
            "org_id": org_id,
        }
        encoded_state = base64.urlsafe_b64encode(json.dumps(state_data).encode("utf-8")).decode("utf-8")

        code_verifier = secrets.token_urlsafe(32)
        m = hashlib.sha256()
        m.update(code_verifier.encode("utf-8"))
        code_challenge = base64.urlsafe_b64encode(m.digest()).decode("utf-8").replace("=", "")

        auth_url = (
            f"{self.authorization_url}&"
            f"state={encoded_state}&"
            f"code_challenge={code_challenge}&"
            f"code_challenge_method=S256"
        )
        await asyncio.gather(
            self.redis_client.add(f"airtable_state:{org_id}:{user_id}", json.dumps(state_data), expire=600),
            self.redis_client.add(f"airtable_verifier:{org_id}:{user_id}", code_verifier, expire=600),
        )

        return auth_url

    async def oauth2callback(self, request: Request) -> HTMLResponse:
        """Callback for the OAuth2 flow"""

        if request.query_params.get("error"):
            raise HTTPException(status_code=400, detail=request.query_params.get("error_description"))

        code = request.query_params.get("code")
        encoded_state = request.query_params.get("state")
        state_data = json.loads(base64.urlsafe_b64decode(encoded_state).decode("utf-8"))

        original_state = state_data.get("state")
        user_id = state_data.get("user_id")
        org_id = state_data.get("org_id")

        saved_state, code_verifier = await asyncio.gather(
            self.redis_client.get(f"airtable_state:{org_id}:{user_id}"),
            self.redis_client.get(f"airtable_verifier:{org_id}:{user_id}"),
        )

        if not saved_state or original_state != json.loads(saved_state).get("state"):
            raise HTTPException(status_code=400, detail="State does not match.")

        async with httpx.AsyncClient() as client:
            response, _, _ = await asyncio.gather(
                client.post(
                    f"{settings.AIRTABLE_OAUTH_URL}/token",
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": self.redirect_uri,
                        "client_id": self.client_id,
                        "code_verifier": code_verifier.decode("utf-8"),
                    },
                    headers={
                        "Authorization": f"Basic {self.encoded_client_id_secret}",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                ),
                self.redis_client.delete(f"airtable_state:{org_id}:{user_id}"),
                self.redis_client.delete(f"airtable_verifier:{org_id}:{user_id}"),
            )

        await self.redis_client.add(f"airtable_credentials:{org_id}:{user_id}", json.dumps(response.json()), expire=600)

        close_window_script = """
        <html>
            <script>
                window.close();
            </script>
        </html>
        """

        return HTMLResponse(content=close_window_script)

    async def get_credentials(self, user_id: str, org_id: str) -> Any:
        """Get the Airtable credentials for the user"""

        credentials = await self.redis_client.get(f"airtable_credentials:{org_id}:{user_id}")
        if not credentials:
            raise HTTPException(status_code=400, detail="No credentials found.")

        credentials = json.loads(credentials)
        await self.redis_client.delete(f"airtable_credentials:{org_id}:{user_id}")

        return credentials

    async def get_items(self, credentials: str) -> List[IntegrationItem]:
        """Fetch the items from the Airtable API"""

        credentials = json.loads(credentials)
        url = f"{settings.AIRTABLE_API_URL}/meta/bases"
        list_of_integration_item_metadata = []
        list_of_responses = []

        self._fetch_items(credentials.get("access_token"), url, list_of_responses)
        for response in list_of_responses:
            list_of_integration_item_metadata.append(self._create_integration_item_metadata_object(response, "Base"))

            async with httpx.AsyncClient() as client:
                tables_response = await client.get(
                    f"{settings.AIRTABLE_API_URL}/meta/bases/{response.get('id')}/tables",
                    headers={"Authorization": f"Bearer {credentials.get('access_token')}"},
                )
                tables_response.raise_for_status()

            if tables_response.status_code == 200:
                tables_response = tables_response.json()
                for table in tables_response["tables"]:
                    list_of_integration_item_metadata.append(
                        self._create_integration_item_metadata_object(
                            table,
                            "Table",
                            response.get("id", None),
                            response.get("name", None),
                        )
                    )

        print_items(
            items=[item.model_dump(mode="json") for item in list_of_integration_item_metadata],
            message="Airtable Integration Items",
        )

        return list_of_integration_item_metadata

    def _create_integration_item_metadata_object(
        self, response_json: str, item_type: str, parent_id: Optional[str] = None, parent_name: Optional[str] = None
    ) -> IntegrationItem:
        """Create the integration item metadata object"""

        parent_id = None if parent_id is None else parent_id + "_Base"
        integration_item_metadata = IntegrationItem(
            id=response_json.get("id", None) + "_" + item_type,
            name=response_json.get("name", None),
            type=item_type,
            parent_id=parent_id,
            parent_path_or_name=parent_name,
        )

        return integration_item_metadata

    def _fetch_items(
        self, access_token: str, url: str, aggregated_response: list, offset: Optional[Any] = None
    ) -> dict:
        """Fetching the list of bases"""

        params = {"offset": offset} if offset is not None else {}
        headers = {"Authorization": f"Bearer {access_token}"}

        with httpx.Client() as client:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()

        if response.status_code == 200:
            results = response.json().get("bases", {})
            offset = response.json().get("offset", None)

            for item in results:
                aggregated_response.append(item)

            if offset is not None:
                self._fetch_items(access_token, url, aggregated_response, offset)
            else:
                return
