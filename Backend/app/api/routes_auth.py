from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timedelta, timezone
from app.db.database import users_collection
from app.db.models.user_model import UserSignup, UserLogin, Token, UserResponse
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from app.core.config import settings
import uuid
import re

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
        "created_at": datetime.now(timezone.utc)
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

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile_data: dict,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update user profile information
    """
    try:
        # Validate input
        full_name = profile_data.get("full_name", "").strip()
        email = profile_data.get("email", "").strip()
        
        if not full_name:
            raise HTTPException(status_code=400, detail="Full name is required")
        
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        # Basic email validation
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Check if email is already taken by another user
        if email != current_user.email:
            existing_user = users_collection.find_one({"email": email, "_id": {"$ne": current_user.id}})
            if existing_user:
                raise HTTPException(status_code=400, detail="Email already registered by another user")
        
        # Update user in database
        update_result = users_collection.update_one(
            {"_id": current_user.id},
            {
                "$set": {
                    "full_name": full_name,
                    "email": email,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        if update_result.modified_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Return updated user info
        return UserResponse(
            id=current_user.id,
            email=email,
            full_name=full_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating profile: {str(e)}")