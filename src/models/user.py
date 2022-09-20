from pydantic import BaseModel, Field
from typing import Optional


class UserModel(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    email: str
    address: Optional[str] = Field(
        None, title="The address of the user", max_length=50
    )

