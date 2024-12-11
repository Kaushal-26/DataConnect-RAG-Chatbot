from fastapi import APIRouter

from controllers.integrations import router as integrations_router

router = APIRouter()
router.include_router(integrations_router)


@router.get("/", tags=["Home"])
def read_root():
    return {"Ping": "Pong"}


@router.get("/health", tags=["Health"])
def health_check():
    return {"health": "ok"}
