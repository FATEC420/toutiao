from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from config.db_conf import get_db
from crud import users


async def get_current_user(
        authorization: str = Header(..., alias="Authorization"),
        db: AsyncSession = Depends(get_db)):
    # 兼容 "Bearer <token>" 与裸 token 两种格式，避免 split(" ")[1] 越界抛 IndexError
    parts = authorization.split(" ")
    token = parts[1] if len(parts) > 1 and parts[0].lower() == "bearer" else parts[-1]
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    user = await users.get_user_by_token(db, token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user
