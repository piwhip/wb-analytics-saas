from fastapi import APIRouter

from app.api.v1 import analytics, auth, demo, sync, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(sync.router)
api_router.include_router(analytics.router)
api_router.include_router(demo.router)
