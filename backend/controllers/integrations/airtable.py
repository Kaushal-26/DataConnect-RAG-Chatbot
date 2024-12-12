from fastapi import APIRouter, Form, Request

from dependencies import AirtableServiceDependency

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
    return await airtable_service.get_credentials(user_id=user_id, org_id=org_id)


@router.post("/load")
async def get_airtable_items(airtable_service: AirtableServiceDependency, credentials: str = Form(...)):
    return await airtable_service.get_items(credentials=credentials)
