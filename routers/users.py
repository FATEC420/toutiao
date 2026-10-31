from fastapi import APIRouter, Depends, Query, HTTPException
from crud import users
from config.db_conf import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from models.users import User
from schemas.users import UserRequest, UserAuthResponse, UserInfoResponse, UserUpdateRequest, UserPasswordUpdateRequest
from utils.auth import get_current_user
from utils.response import success_response

router = APIRouter(prefix="/api/user", tags=["user"])


@router.post("/register")
async def register(user_data: UserRequest, db: AsyncSession = Depends(get_db)):
    exist_user = await users.get_user_by_username(db, user_data.username)
    if exist_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = await users.create_user(db, user_data)
    token = await users.generate_token(db, new_user.id)

    response_data = UserAuthResponse(token=token, user_info=UserInfoResponse.model_validate(new_user))
    return success_response(message="注册成功", data=response_data.model_dump())


@router.post("/login")
async def login(user_data: UserRequest, db: AsyncSession = Depends(get_db)):
    user = await users.get_user_by_username_and_password(db, user_data)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = await users.generate_token(db, user.id)

    response_data = UserAuthResponse(token=token, user_info=UserInfoResponse.model_validate(user))
    return success_response(message="注册成功", data=response_data)


# 依赖注入token验证
@router.get("/info")
async def get_user_info(user: User = Depends(get_current_user)):
    return success_response(message="获取个人信息成功", data=UserInfoResponse.model_validate(user))


@router.put("/update")
async def update_user_info(
        user_data: UserUpdateRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    updated_user = await users.update_user(db, user.username, user_data)
    return success_response(message="更新个人信息成功", data=UserInfoResponse.model_validate(updated_user))


@router.put("/password")
async def update_user_password(
        password_data: UserPasswordUpdateRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    res = await users.update_password(db, user, password_data)
    if not res:
        raise HTTPException(status_code=400, detail="修改密码失败")
    return success_response(message="修改密码成功", data=None)
