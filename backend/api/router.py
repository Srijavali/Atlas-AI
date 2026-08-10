from fastapi import APIRouter

from backend.api.routes.telegram import router as telegram_router

api_router = APIRouter()

api_router.include_router(telegram_router)