from fastapi import APIRouter

from .airtable import router as airtable_router
from .hubspot import router as hubspot_router
from .notion import router as notion_router

router = APIRouter(prefix="/integrations")

router.include_router(airtable_router)
router.include_router(hubspot_router)
router.include_router(notion_router)
