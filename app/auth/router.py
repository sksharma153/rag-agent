from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.errors import DuplicateKeyError
from app.auth.dependencies import get_current_user

from app.auth.models import UserRole
from app.auth.schemas import LoginRequest, SignupRequest, TokenResponse, UserResponse
from app.auth.security import verify_password, hash_password, create_access_token
from app.database import users_collection

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

def build_user_response(
        user: dict
) -> UserResponse:
    return UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        full_name=user["full_name"],
        role=user["role"],
        is_active=user["is_active"]
    )

@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def signup(
        request: SignupRequest
):
    existing_user = users_collection.find_one({"email": request.email.lower()})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = {
        "email": request.email.lower(),
        "full_name": request.full_name,
        "password_hash": hash_password(request.password),
        "role": UserRole.USER.value,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
    }

    try:
        result = users_collection.insert_one(user)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user["_id"] = result.inserted_id
    return build_user_response(user)

@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(request: LoginRequest):
    user = users_collection.find_one(
        {
            "email": request.email.lower()
        }
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    access_token = create_access_token(
        user_id=str(user["_id"]),
        role=user["role"],
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=build_user_response(user),
    )

@router.get(
    "/me",
    response_model=UserResponse,
)
def me(
        current_user: dict = Depends(get_current_user)
):
    return build_user_response(current_user)