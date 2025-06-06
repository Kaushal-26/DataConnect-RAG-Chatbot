from typing import List

from fastapi import APIRouter, Form, Request

from dependencies import AirtableServiceDependency
from schemas import IntegrationItem

router = APIRouter(prefix="/airtable", tags=["Airtable Integration Routes"])


# Airtable
@router.post("/authorize")
async def authorize_airtable_integration(
    airtable_service: AirtableServiceDependency, user_id: str = Form(...), org_id: str = Form(...)
):
    return await airtable_service.authorize(user_id=user_id, org_id=org_id)


@router.get("/oauth2callback")
async def oauth2callback_airtable_integration(request: Request, airtable_service: AirtableServiceDependency):
    return await airtable_service.oauth2callback(request=request)


@router.post("/credentials")
async def get_airtable_credentials_integration(
    airtable_service: AirtableServiceDependency, user_id: str = Form(...), org_id: str = Form(...)
):
    # Return true if credentials are found, false otherwise
    return len(await airtable_service.get_credentials(user_id=user_id, org_id=org_id)) > 0


@router.post("/load", response_model=List[IntegrationItem])
async def get_airtable_items(
    airtable_service: AirtableServiceDependency, user_id: str = Form(...), org_id: str = Form(...)
):
    return await airtable_service.get_items(user_id=user_id, org_id=org_id)
