# Uncomment to see debug logs
import logging
import os
import sys

from llama_index.core import (
    Document,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.core.chat_engine.types import BaseChatEngine, ChatMode
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.storage.index_store import SimpleIndexStore
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

from config import settings

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

CUSTOM_CHAT_HISTORY = [
    ChatMessage(
        role=MessageRole.USER,
        content=(
            "You should always run the tool before giving any response. "
            "Always be descriptive and give formatted response to me."
            "Do not tell me about the tool you are using."
        ),
    ),
]


# https://docs.llamaindex.ai/en/stable/examples/vector_stores/SimpleIndexDemo/
class RAGEngine:
    def __init__(self):
        if settings.OPENAI_API_KEY is None:
            raise ValueError("Please set OPENAI_API_KEY in .env file, for AI service to work")

        self.llm = OpenAI(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_CHAT_MODEL)
        self.embed_model = OpenAIEmbedding(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_EMBEDDING_MODEL)

    async def add_data(self, user_id: str, org_id: str, data: str, metadata: dict = {}):
        document = Document(text=data, metadata=metadata)
        index = await self.load_index(user_id, org_id)
        index.insert(document)
        index.storage_context.persist(persist_dir=f"{settings.RAG_STORAGE_PATH}/org_{org_id}/user_{user_id}")

    async def load_index(self, user_id: str, org_id: str) -> VectorStoreIndex:
        """
        Load the index for the user and org
        If the index is not found, create a new index with the user and org id
        """

        index_id = f"vector_index_org:{org_id}_user:{user_id}"
        user_storage_path = f"{settings.RAG_STORAGE_PATH}/org_{org_id}/user_{user_id}"

        if not os.path.exists(user_storage_path):
            # Create a new index for the user if it doesn't exist
            storage_context = StorageContext.from_defaults(
                docstore=SimpleDocumentStore(),
                vector_store=SimpleVectorStore(),
                index_store=SimpleIndexStore(),
            )
            index = VectorStoreIndex.from_documents(
                documents=[], storage_context=storage_context, embed_model=self.embed_model, verbose=True
            )
            index.set_index_id(index_id)
            # Persist the index to the local storage
            index.storage_context.persist(persist_dir=user_storage_path)
        else:
            # Load the existing index for the user
            storage_context = StorageContext.from_defaults(persist_dir=user_storage_path)
            index = load_index_from_storage(storage_context, index_id=index_id, embed_model=self.embed_model)

        return index

    async def load_chat_engine(self, index: VectorStoreIndex, chat_memory: ChatMemoryBuffer) -> BaseChatEngine:
        # Chat engine with the index with mode REACT and memory from the local chat store
        return index.as_chat_engine(
            chat_mode=ChatMode.REACT,
            llm=self.llm,
            memory=chat_memory,
            verbose=True,
        )

    async def load_chat_memory(self, chat_store: SimpleChatStore, chat_store_key: str) -> ChatMemoryBuffer:
        # Load the chat memory from the local storage
        return ChatMemoryBuffer.from_defaults(
            chat_history=CUSTOM_CHAT_HISTORY,
            llm=self.llm,
            chat_store=chat_store,
            chat_store_key=chat_store_key,
            token_limit=settings.CHAT_MEMORY_TOKEN_LIMIT,
        )

    async def chat(self, user_id: str, org_id: str, chat_session_id: str, message: str) -> str:
        # Fetch chat store from the local storage
        chat_store = SimpleChatStore.from_persist_path(
            persist_path=f"{settings.RAG_STORAGE_PATH}/org_{org_id}/user_{user_id}/chat_session_{chat_session_id}.json"
        )

        # Load the chat memory from the local storage
        chat_memory = await self.load_chat_memory(
            chat_store=chat_store, chat_store_key=f"org:{org_id}_user:{user_id}_session:{chat_session_id}"
        )

        # Load the index
        index = await self.load_index(user_id=user_id, org_id=org_id)

        # Fetch or create the chat engine with the index and the chat memory
        chat_engine = await self.load_chat_engine(index=index, chat_memory=chat_memory)

        # Chat with the engine
        response = chat_engine.chat(message)

        # Save the chat history to the local storage
        chat_store.persist(
            persist_path=f"{settings.RAG_STORAGE_PATH}/org_{org_id}/user_{user_id}/chat_session_{chat_session_id}.json"
        )

        # Save the index to the local storage
        index.storage_context.persist(persist_dir=f"{settings.RAG_STORAGE_PATH}/org_{org_id}/user_{user_id}")
        return response
