from pydantic import BaseModel

from app.schemas.user import UserResponse


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CurrentUserResponse(UserResponse):
    role_name: str | None = None