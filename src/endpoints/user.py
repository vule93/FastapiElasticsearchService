from curses.ascii import US
from fastapi import APIRouter
from fastapi import Query
from src.models.user import UserModel
from typing import Optional

# APIRouter creates path operations for user module
router = APIRouter(
    prefix="/users",
    tags=["User"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
async def read_root():
    return [{"id": 1}, {"id": 2}]


@router.get("/{user_id}")
async def read_user(user_id: int):
    return {"id": user_id, "full_name": "Danny Manny", "email": "danny.manny@gmail.com"}


@router.get("/{user_id}/detail")
async def read_users(user_id: int, q: Optional[str] = Query(None, max_length=50)):
    results = {"users": [{"id": user_id}, {"id": user_id}]}
    if q:
        results.update({"q": q})
    return results


@router.post("/add")
async def add_user(user: UserModel):
    return {"full_name": user.first_name+" "+user.last_name}


@router.put("/update")
async def read_user(user: UserModel):
    return {"id": user.user_id, "full_name": user.first_name+" "+user.last_name, "email": user.email}


@router.delete("/{user_id}/delete")
async def read_user(user_id: int):
    return {"id": user_id, "is_deleted": True}
