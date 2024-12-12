import logging
import json
from fastapi import HTTPException, status
from jose import jwt, JWTError
import os
from dotenv import load_dotenv

from lib.create_token import get_user
from model.model import TokenData
load_dotenv()

db = os.getenv("users_db")
db = json.loads(db)
key = os.getenv("SECRET_KEY")
algo = os.getenv("ALGORITHM")


def verify_password(plain_password, hashed_password):
    try:
        print("Inside verify password function")
        if plain_password == hashed_password:
            print("PASSWORD VERIFIED")
            return True
        else:
            print("PASSWORD INCORRECT")
            return False
    except Exception as err:
        print(f"Error in verify password function --> {err}")
        raise RuntimeError


def authenticate_user(db, username: str, password: str):
    try:
        print("Inside authenticate user function")
        user = get_user(db, username)
        print("USER AVAILABLE")
        if not user:
            print("USER NOT AVAILABLE")
            return False
        if not verify_password(password, user.hashed_password):
            print("PASSWORD IS INCORRECT")
            return False
        return user
    except Exception as err:
        print(f"Error in authenticate user function --> {err}")
        raise RuntimeError
        


async def get_current_user(token):
    try:
        print("Inside get current user function")
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        # print(f"token-----------\n\n{token}\n\n")
        try:
            payload = jwt.decode(token['access_token'], key, algorithms=[algo])
            username: str = payload.get("sub")
            if username is None:
                print(
                    f"IN GET CURRENT USER --> USER NAME IS NONE --> {credentials_exception}")
                raise credentials_exception
            token_data = TokenData(username=username)
        except JWTError:
            print(
                f"IN GET CURRENT USER --> JWT ERROR EXCEPTION --> {credentials_exception}")
            raise credentials_exception
        user = get_user(db, username=token_data.username)
        if user is None:
            print(
                f"IN GET CURRENT USER --> USER IS NONE --> {credentials_exception}")
            raise credentials_exception
        return user
    except Exception as err:
        print(f"Error in get current user function --> {err}")
        raise RuntimeError
        


async def get_current_active_user(token):
    try:
        current_user = await get_current_user(token)
        print("GETTING CURRENT USER")
        # print(current_user)
        if current_user.disabled:
            print("Feature is disabled for the user")
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user
    except Exception as err:
        print(f"Error in get_current_active_user function --> {err}")
        raise RuntimeError
