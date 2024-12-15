import asyncio
import base64
import json
import secrets
from typing import List

import httpx
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse
from hubspot import HubSpot

from config import settings
from schemas import IntegrationItem
from utils import rich_print_json

from .base import BaseIntegrationService


class HubspotService(BaseIntegrationService):
    """Hubspot integration service inherits from BaseIntegrationService"""

    async def authorize(self, user_id: str, org_id: str) -> str:
        """Authorize the user to access the Hubspot API"""

        state_data = {
            "state": secrets.token_urlsafe(32),
            "user_id": user_id,
            "org_id": org_id,
        }
        encoded_state = base64.urlsafe_b64encode(json.dumps(state_data).encode("utf-8")).decode("utf-8")

        auth_url = f"{self.authorization_url}&state={encoded_state}"
        await self.redis_client.add(f"hubspot_state:{org_id}:{user_id}", json.dumps(state_data), expire=600)

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

        saved_state = await self.redis_client.get(f"hubspot_state:{org_id}:{user_id}")

        if not saved_state or original_state != json.loads(saved_state).get("state"):
            raise HTTPException(status_code=400, detail="State does not match.")

        # Get the access token
        async with httpx.AsyncClient() as client:
            response, _ = await asyncio.gather(
                client.post(
                    f"{settings.HUBSPOT_API_URL}/oauth/v1/token",
                    data={
                        "grant_type": "authorization_code",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "redirect_uri": self.redirect_uri,
                        "code": code,
                    },
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                ),
                self.redis_client.delete(f"hubspot_state:{org_id}:{user_id}"),
            )
            response.raise_for_status()

        await self.redis_client.add(f"hubspot_credentials:{org_id}:{user_id}", json.dumps(response.json()), expire=600)

        close_window_script = """
        <html>
            <script>
                window.close();
            </script>
        </html>
        """

        return HTMLResponse(content=close_window_script)

    async def get_credentials(self, user_id: str, org_id: str) -> dict:
        """
        Get the HubSpot credentials for the user
        """

        credentials = await self.redis_client.get(f"hubspot_credentials:{org_id}:{user_id}")
        if not credentials:
            raise HTTPException(status_code=400, detail="No credentials found for HubSpot integration.")

        return json.loads(credentials)

    async def get_items(self, user_id: str, org_id: str) -> List[IntegrationItem]:
        """
        Fetch the items from HubSpot API
        - Here we are fetching the contacts of the companies as integration items.
        """

        credentials = await self.get_credentials(user_id, org_id)
        api_client = HubSpot(access_token=credentials.get("access_token"))

        list_of_integration_item_metadata = []

        companies_with_contacts = await self._fetch_contacts_of_companies(api_client)
        for company in companies_with_contacts:
            contact_ids = [
                contact.get("id")
                for contact in company.get("associations").get("contacts").get("results")
                if contact.get("type") == "company_to_contact"
            ]

            # Make a batch async API call to fetch the contacts
            tasks_fetch_contacts = [
                self._fetch_item_as_hubspot_contact(api_client, contact_id) for contact_id in contact_ids
            ]
            fetched_contacts = await asyncio.gather(*tasks_fetch_contacts)

            # Make integration item metadata objects asynchronously
            tasks_make_integration_item_metadata = [
                self._create_integration_item_metadata_object(contact, company) for contact in fetched_contacts
            ]
            new_integration_item_metadata = await asyncio.gather(*tasks_make_integration_item_metadata)

            list_of_integration_item_metadata.extend(new_integration_item_metadata)

        items_json = "\n".join([item.model_dump_json(indent=4) for item in list_of_integration_item_metadata])
        rich_print_json(items_json, "Hubspot Integration Items")

        # Add the items to the RAG engine in a coroutine without blocking the main thread
        if self.rag_engine is not None:
            asyncio.create_task(
                self.add_integration_items_to_rag(
                    user_id=user_id,
                    org_id=org_id,
                    items_json=items_json,
                    integration_type="Hubspot",
                )
            )

        return list_of_integration_item_metadata

    async def _fetch_contacts_of_companies(self, api_client: HubSpot):
        """
        Fetch the contacts of the companies
        """

        companies_with_contacts = api_client.crm.companies.get_all(associations=["contacts"])
        companies_with_contacts = [company.to_dict() for company in companies_with_contacts]
        return companies_with_contacts

    async def _fetch_item_as_hubspot_contact(self, api_client: HubSpot, contact_id: str):
        """
        Fetch the contact of the company
        """

        contact = api_client.crm.contacts.basic_api.get_by_id(contact_id)
        return contact.to_dict()

    async def _create_integration_item_metadata_object(self, contact: dict, company: dict) -> IntegrationItem:
        """
        Create the integration item metadata object
        """

        response = IntegrationItem(
            id=contact.get("id"),
            type="hubspot_contacts_of_companies",
            name=f"{contact.get('properties').get('firstname')} {contact.get('properties').get('lastname')}",
            parent_id=company.get("id"),
            parent_path_or_name=company.get("properties").get("name"),
            creation_time=contact.get("created_at"),
            last_modified_time=contact.get("updated_at"),
            visibility=not contact.get("archived"),
        )

        return response
