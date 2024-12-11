# slack.py

import asyncio
import base64
import json
import os
import secrets
from fastapi import HTTPException, Request

from dotenv import load_dotenv
from fastapi.responses import HTMLResponse
import httpx

from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, delete_key_redis, get_value_redis
from hubspot import HubSpot

load_dotenv()

CLIENT_ID = os.getenv("HUBSPOT_CLIENT_ID")
CLIENT_SECRET = os.getenv("HUBSPOT_CLIENT_SECRET")

REDIRECT_URI = "http://localhost:8000/integrations/hubspot/oauth2callback"
SCOPES = "crm.objects.contacts.read crm.objects.companies.read"
authorization_url = f"https://app.hubspot.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={SCOPES}"


async def authorize_hubspot(user_id: str, org_id: str):
    """
    Authorize the user to HubSpot
    """
    state_data = {
        "state": secrets.token_urlsafe(32),
        "user_id": user_id,
        "org_id": org_id,
    }
    encoded_state = base64.urlsafe_b64encode(json.dumps(state_data).encode("utf-8")).decode("utf-8")

    auth_url = f"{authorization_url}&state={encoded_state}"
    await add_key_value_redis(f"hubspot_state:{org_id}:{user_id}", json.dumps(state_data), expire=600)

    return auth_url


async def oauth2callback_hubspot(request: Request):
    """
    Handle the OAuth2 callback for HubSpot
    """
    if request.query_params.get("error"):
        raise HTTPException(status_code=400, detail=request.query_params.get("error_description"))

    code = request.query_params.get("code")
    encoded_state = request.query_params.get("state")
    state_data = json.loads(base64.urlsafe_b64decode(encoded_state).decode("utf-8"))
    
    original_state = state_data.get("state")
    user_id = state_data.get("user_id")
    org_id = state_data.get("org_id")

    saved_state = await get_value_redis(f"hubspot_state:{org_id}:{user_id}")

    if not saved_state or original_state != json.loads(saved_state).get("state"):
        raise HTTPException(status_code=400, detail="State does not match.")

    # Get the access token
    async with httpx.AsyncClient() as client:
        response, _ = await asyncio.gather(
            client.post(
                "https://api.hubapi.com/oauth/v1/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "redirect_uri": REDIRECT_URI,
                    "code": code,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            ),
            delete_key_redis(f'hubspot_state:{org_id}:{user_id}'),
        )
        response.raise_for_status()
    
    await add_key_value_redis(f"hubspot_credentials:{org_id}:{user_id}", json.dumps(response.json()), expire=600)

    close_window_script = """
    <html>
        <script>
            window.close();
        </script>
    </html>
    """

    return HTMLResponse(content=close_window_script)

async def get_hubspot_credentials(user_id, org_id):
    """
    Get the HubSpot credentials for the user
    """
    credentials = await get_value_redis(f"hubspot_credentials:{org_id}:{user_id}")
    if not credentials:
        raise HTTPException(status_code=400, detail="No credentials found for HubSpot integration.")
    
    credentials = json.loads(credentials)
    if not credentials:
        raise HTTPException(status_code=400, detail="No credentials found for HubSpot integration.")
    
    await delete_key_redis(f"hubspot_credentials:{org_id}:{user_id}")

    return credentials

async def fetch_contacts_of_companies(api_client: HubSpot):
    """
    Fetch the contacts of the companies
    """
    companies_with_contacts = api_client.crm.companies.get_all(associations=["contacts"])
    companies_with_contacts = [company.to_dict() for company in companies_with_contacts]
    return companies_with_contacts

async def fetch_item_as_hubspot_contact(api_client: HubSpot, contact_id: str):
    """
    Fetch the contact of the company
    """
    contact = api_client.crm.contacts.basic_api.get_by_id(contact_id)
    return contact.to_dict()

async def create_integration_item_metadata_object(contact: dict, company: dict) -> IntegrationItem:
    """
    Create the integration item metadata object
    """
    response = IntegrationItem(
        id=contact.get("id"),
        type="hubspot_contacts_of_company",
        name=f"{contact.get('properties').get('firstname')} {contact.get('properties').get('lastname')}",
        parent_id=company.get("id"),
        parent_path_or_name=company.get("properties").get("name"),
        creation_time=contact.get("created_at"),
        last_modified_time=contact.get("updated_at"),
        visibility=not contact.get("archived"),
    )
    return response

async def get_items_hubspot(credentials: str):
    """
    Get the items from HubSpot
    - Here we are fetching the contacts of the companies as integration items.
    """

    credentials = json.loads(credentials)
    api_client = HubSpot(access_token=credentials.get("access_token"))

    list_of_integration_item_metadata = []

    companies_with_contacts = await fetch_contacts_of_companies(api_client)
    for company in companies_with_contacts:
        contact_ids = [
            contact.get("id") for contact in company.get("associations").get("contacts").get("results")
            if contact.get("type") == "company_to_contact"
        ]

        # Make a batch async API call to fetch the contacts
        tasks_fetch_contacts = [
            fetch_item_as_hubspot_contact(api_client, contact_id)
            for contact_id in contact_ids
        ]
        fetched_contacts = await asyncio.gather(*tasks_fetch_contacts)

        # Make integration item metadata objects asynchronously
        tasks_make_integration_item_metadata = [
            create_integration_item_metadata_object(contact, company)
            for contact in fetched_contacts
        ]
        new_integration_item_metadata = await asyncio.gather(*tasks_make_integration_item_metadata)

        list_of_integration_item_metadata.extend(new_integration_item_metadata)

    print(list_of_integration_item_metadata)

    return list_of_integration_item_metadata

