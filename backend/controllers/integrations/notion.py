from fastapi import APIRouter, Form, Request

from dependencies import NotionServiceDependency

router = APIRouter(prefix="/notion", tags=["Notion Integration Routes"])


# Notion
@router.post("/authorize")
async def authorize_notion_integration(
    notion_service: NotionServiceDependency, user_id: str = Form(...), org_id: str = Form(...)
):
    return await notion_service.authorize(user_id, org_id)


@router.get("/oauth2callback")
async def oauth2callback_notion_integration(request: Request, notion_service: NotionServiceDependency):
    return await notion_service.oauth2callback(request)


@router.post("/credentials")
async def get_notion_credentials_integration(
    notion_service: NotionServiceDependency, user_id: str = Form(...), org_id: str = Form(...)
):
    return await notion_service.get_credentials(user_id, org_id)


@router.post("/load")
async def get_notion_items(notion_service: NotionServiceDependency, credentials: str = Form(...)):
    return await notion_service.get_items(credentials)
