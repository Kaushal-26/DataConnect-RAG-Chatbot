from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from controllers import router


def create_server():
    app = FastAPI()
    app.include_router(router)

    origins = [
        settings.FRONTEND_URL,  # React app address
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = create_server()
