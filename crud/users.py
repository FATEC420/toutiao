from datetime import datetime, timedelta
import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from schemas.users import UserRequest, UserUpdateRequest, UserPasswordUpdateRequest
from utils import security

from models.users import User, UserToken


async def get_user_by_username(db: AsyncSession, username: str):
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_data: UserRequest):
    hashed_password = security.get_password_hash(user_data.password)
    user = User(username=user_data.username, password=hashed_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# 生成token
async def generate_token(db: AsyncSession, user_id: int):
    token = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(days=3)
    query = select(UserToken).where(UserToken.user_id == user_id)
    result = await db.execute(query)
    user_token = result.scalar_one_or_none()

    if user_token:
        user_token.token = token
        user_token.expires_at = expires_at
    else:
        user_token = UserToken(user_id=user_id, token=token, expires_at=expires_at)
        db.add(user_token)
        await db.commit()
        # await db.refresh(user_token)

    return token


async def get_user_by_username_and_password(db: AsyncSession, user_data: UserRequest):
    user = await get_user_by_username(db, user_data.username)
    if not user:
        return None
    if not security.verify_password(user_data.password, user.password):
        return None
    return user


async def get_user_by_token(db: AsyncSession, token: str):
    query = select(UserToken).where(UserToken.token == token)
    result = await db.execute(query)
    db_token = result.scalar_one_or_none()

    if not db_token or db_token.expires_at < datetime.now():
        return None

    stmt = select(User).where(User.id == db_token.user_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


async def update_user(db: AsyncSession, username: str, user_data: UserUpdateRequest):
    stmt = update(User).where(User.username == username).values(**user_data.model_dump(
        exclude_unset=True,
        exclude_none=True
    ))
    result = await db.execute(stmt)
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="User not found")

    user = await get_user_by_username(db, username)
    return user


async def update_password(db: AsyncSession, user: User, password_data: UserPasswordUpdateRequest):
    if not security.verify_password(password_data.old_password, user.password):
        return False
    user.password = security.get_password_hash(password_data.new_password)
    # 更新:由SQLAlchemy真正接管这个User 对象，确保可以 commit
    # 规避 session过期或关闭导致的不能提交的问题
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return True
