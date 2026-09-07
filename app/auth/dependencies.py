from bson.errors import InvalidId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from bson import ObjectId
from bson.objectid import ObjectId

from app.auth.models import UserRole
from app.auth.security import decode_access_token
from app.database import users_collection

bearer_schema = HTTPBearer(
    auto_error=True,
)

def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_schema),
) -> dict:

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    user_id = payload["sub"]

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    try:
        object_id = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID",
        )
    user = users_collection.find_one({"_id": object_id})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user

def require_admin(
        current_user: dict = Depends(get_current_user),
) -> dict:
    if (
            current_user.get("role") != UserRole.ADMIN.value
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin Access Required",
        )
    return current_user