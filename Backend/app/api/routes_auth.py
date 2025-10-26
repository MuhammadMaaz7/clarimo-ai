from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timedelta
from app.db.database import users_collection
from app.db.models.user_model import UserSignup, UserLogin, Token, UserResponse
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from app.core.config import settings
import uuid

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(user: UserSignup):
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    hashed_password = hash_password(user.password)

    user_doc = {
        "_id": user_id,
        "email": user.email,
        "full_name": user.full_name,
        "hashed_password": hashed_password,
        "created_at": datetime.utcnow()
    }

    users_collection.insert_one(user_doc)

    access_token = create_access_token(data={"sub": user_id})
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(id=user_id, email=user.email, full_name=user.full_name)
    )

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    user = users_collection.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token = create_access_token(data={"sub": str(user["_id"])})
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(id=str(user["_id"]), email=user["email"], full_name=user["full_name"])
    )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user

@router.get("/validate-token")
async def validate_token(current_user: UserResponse = Depends(get_current_user)):
    """
    Validate if the current token is still valid.
    Returns user info if valid, 401 if expired/invalid.
    Frontend can use this to check token status.
    """
    return {
        "valid": True,
        "user": current_user,
        "message": "Token is valid"
    }
