from typing import List

from fastapi import APIRouter, Form, Request

from dependencies import HubspotServiceDependency
from schemas import IntegrationItem

router = APIRouter(prefix="/hubspot", tags=["HubSpot Integration Routes"])


# HubSpot
@router.post("/authorize")
async def authorize_hubspot_integration(
    hubspot_service: HubspotServiceDependency, user_id: str = Form(...), org_id: str = Form(...)
):
    return await hubspot_service.authorize(user_id, org_id)


@router.get("/oauth2callback")
async def oauth2callback_hubspot_integration(request: Request, hubspot_service: HubspotServiceDependency):
    return await hubspot_service.oauth2callback(request)


@router.post("/credentials")
async def get_hubspot_credentials_integration(
    hubspot_service: HubspotServiceDependency, user_id: str = Form(...), org_id: str = Form(...)
):
    # Return true if credentials are found, false otherwise
    return len(await hubspot_service.get_credentials(user_id, org_id)) > 0


@router.post("/load", response_model=List[IntegrationItem])
async def load_slack_data_integration(
    hubspot_service: HubspotServiceDependency, user_id: str = Form(...), org_id: str = Form(...)
):
    return await hubspot_service.get_items(user_id=user_id, org_id=org_id)
