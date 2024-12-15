from fastapi import APIRouter, Form

from dependencies import AIServiceDependency
from schemas import ChatMessage

router = APIRouter(prefix="/chat", tags=["Chat Routes"])


@router.post("", response_model=ChatMessage)
async def chat(
    ai_service: AIServiceDependency,
    user_id: str = Form(...),
    org_id: str = Form(...),
    chat_session_id: str = Form(...),
    message: str = Form(...),
):
    return await ai_service.chat(user_id=user_id, org_id=org_id, chat_session_id=chat_session_id, message=message)
