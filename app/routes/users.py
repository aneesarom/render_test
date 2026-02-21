from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from app.supabase.supabase_client import supabase
from app.auth.jwt_handler import hash_password, verify_password, create_access_token
from app.auth.dependencies import get_current_user
from datetime import datetime, timezone

router = APIRouter(prefix="/users", tags=["users"])


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    is_admin: bool

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UpdateUserRequest(BaseModel):
    email: EmailStr
    password: str
    is_admin: bool


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    is_admin: bool


@router.post("/signup")
def signup(data: SignUpRequest):
    existing = supabase.table("users").select("*").eq("email", data.email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(data.password)

    res = supabase.table("users").insert({
        "email": data.email,
        "password": hashed_password,
        "is_admin": data.is_admin
    }).execute()

    if not res.data:
        raise HTTPException(status_code=400, detail="Signup failed")

    user = res.data[0]
    access_token = create_access_token(user["id"])

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/login")
def login(data: LoginRequest):
    res = supabase.table("users").select("*").eq("email", data.email).execute()

    if not res.data:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = res.data[0]

    if not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(user["id"])

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.put("/{user_id}")
def update_user(user_id: str, data: UpdateUserRequest, current_user: dict = Depends(get_current_user)):
    if current_user["id"] != user_id and not current_user["is_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = {}

    update_data["email"] = data.email
    update_data["password"] = hash_password(data.password)
    update_data["is_admin"] = data.is_admin
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()


    res = supabase.table("users").update(update_data).eq("id", user_id).execute()

    print(res)

    if not res.data:
        raise HTTPException(status_code=400, detail="Update failed")

    return {"message": "User updated successfully"}


@router.delete("/{user_id}")
def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["id"] != user_id and not current_user["is_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    res = supabase.table("users").delete().eq("id", user_id).execute()

    if not res.data:
        raise HTTPException(status_code=400, detail="Delete failed")

    return {"message": "User deleted successfully"}