from fastapi import APIRouter, Form, Request

from integrations.hubspot import (
    authorize_hubspot,
    get_hubspot_credentials,
    get_items_hubspot,
    oauth2callback_hubspot,
)

router = APIRouter(prefix="/hubspot", tags=["HubSpot Integration Routes"])


# HubSpot
@router.post("/authorize")
async def authorize_hubspot_integration(user_id: str = Form(...), org_id: str = Form(...)):
    return await authorize_hubspot(user_id, org_id)


@router.get("/oauth2callback")
async def oauth2callback_hubspot_integration(request: Request):
    return await oauth2callback_hubspot(request)


@router.post("/credentials")
async def get_hubspot_credentials_integration(user_id: str = Form(...), org_id: str = Form(...)):
    return await get_hubspot_credentials(user_id, org_id)


@router.post("/load")
async def load_slack_data_integration(credentials: str = Form(...)):
    return await get_items_hubspot(credentials)
