from fastapi import APIRouter, Depends, Query, HTTPException
from crud import favorite
from config.db_conf import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from models.users import User
from schemas.favorite import FavoriteCheckResponse, FavoriteAllRequest, FavoriteListResponse
from utils.auth import get_current_user
from utils.response import success_response

router = APIRouter(prefix="/api/favorite", tags=["favorite"])


@router.get("/check")
async def check_favorite(
        news_id: int = Query(..., alias="newsId"),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)):
    # 获取数据库里的新闻分类
    is_favorite = await favorite.check_favorite(db, user.id, news_id)
    return success_response(message="检查收藏状态成功", data=FavoriteCheckResponse(isFavorite=is_favorite))


@router.post("/add")
async def add_favorite(
        news_data: FavoriteAllRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)):
    # 已收藏则直接返回，避免重复插入
    if await favorite.check_favorite(db, user.id, news_data.news_id):
        return success_response(message="已收藏", data=True)

    # 真正写入数据库
    new_favorite = await favorite.add_favorite(db, user.id, news_data.news_id)
    return success_response(message="收藏成功", data=new_favorite.id)


@router.delete("/remove")
async def remove_favorite(
        news_id: int = Query(..., alias="newsId"),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)):
    # 获取数据库里的新闻分类
    result = await favorite.remove_favorite(db, user.id, news_id)
    if not result:
        raise HTTPException(status_code=404, detail="收藏记录不存在")
    return success_response(message="取消收藏成功", data=result)


@router.get("/list")
async def get_favorite_list(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, alias="pageSize", le=100),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    rows, total = await favorite.get_favorite_list(db, user.id, page, page_size)
    favorite_list = [{
        **news.__dict__,
        "favorite_time": favorite_time,
        "favorite_id": favorite_id
    } for news, favorite_time, favorite_id in rows]
    has_more = total > page * page_size
    data = FavoriteListResponse(list=favorite_list, hasMore=has_more, total=total)
    return success_response(message="获取收藏列表成功", data=data)


@router.delete("/clear")
async def clear_favorite(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)):
    count = await favorite.clear_favorite(db, user.id)
    return success_response(message=f"清空了{count}条收藏记录")
