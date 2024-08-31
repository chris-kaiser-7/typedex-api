from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    login,
    users,
    proxy,
    books,
    assistant,
    subtype
)

api_router = APIRouter()
api_router.include_router(login.router, prefix="/login", tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(proxy.router, prefix="/proxy", tags=["proxy"])
api_router.include_router(books.router)
api_router.include_router(assistant.router, prefix="/assistant", tags=["assistant"])
api_router.include_router(subtype.router, prefix="/subtype", tags=["subtype"])
