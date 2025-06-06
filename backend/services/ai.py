from rag import RAGEngine
from schemas import ChatMessage


class AIService:
    def __init__(self, rag_engine: RAGEngine):
        self.rag_engine = rag_engine

    async def chat(self, user_id: str, org_id: str, chat_session_id: str, message: str):
        message = await self.rag_engine.chat(
            user_id=user_id, org_id=org_id, chat_session_id=chat_session_id, message=message
        )
        return ChatMessage(message=message.response, role="ASSISTANT")
