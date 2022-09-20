from fastapi import APIRouter
from src.endpoints import user

router = APIRouter()
router.include_router(user.router)