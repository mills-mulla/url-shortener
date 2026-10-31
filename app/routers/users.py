from fastapi import APIRouter , Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.schemas import UserCreate,UserCreated
from app.db import get_db
from app.models import User
from app.services.security import new_api_key

router = APIRouter(prefix="/v1/users", tags=["users"])

@router.post("", response_model= UserCreated, status_code=201)
async def create_user(body: UserCreate, db: AsyncSession = Depends(get_db)):
    key, key_hash = new_api_key()
    user = User(email=body.email.lower(),  api_key_hash=key_hash)
    db.add(user)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(ststus_code=409, detail="Email already registered")
    return UserCreated(id=user.id, email=user.email, api_key=key)
