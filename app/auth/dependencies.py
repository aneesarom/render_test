from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import os
from app.logging_config import set_user_id
from app.supabase.supabase_client import supabase
from app.logging_config import get_logger, set_user_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"


def get_current_user(token: str = Depends(oauth2_scheme)):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    res = supabase.table("users").select("id, email, is_admin").eq("id", user_id).execute()

    if not res.data:
        raise credentials_exception
    print("asdasdasd", user_id)
    set_user_id(user_id)
    return res.data[0]