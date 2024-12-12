import logging
from datetime import datetime, timedelta
from urllib.error import ContentTooShortError
from jose import jwt
from model.model import UserInDB
import os
from dotenv import load_dotenv
load_dotenv()

key = os.getenv("SECRET_KEY")
algo = os.getenv("ALGORITHM")


def get_user(db, username: str):
    try:
        print("inside get user function")
        if username in db:
            user_dict = db[username]
            return UserInDB(**user_dict)
    except Exception as err:
        print(f"Error in get user function --> {err}")
        raise RuntimeError


def create_access_token(data: dict, expires_delta: timedelta = None):
    try:
        print("Inside create access token function")
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        try:
            encoded_jwt = jwt.encode(to_encode, str(key), algorithm=str(algo))
            return encoded_jwt
        except Exception as err:
            print(f"Error in creating token --> {err}")
            raise ContentTooShortError
    except Exception as err:
        print(f"Error in create access token function --> {err}")
        raise RuntimeError
