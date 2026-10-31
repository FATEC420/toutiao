from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, insert, delete
from models.favorite import Favorite
from models.news import News

from utils.auth import get_current_user


async def check_favorite(db: AsyncSession, user_id: int, news_id: int) -> bool:
    stmt = select(Favorite.id).where(Favorite.user_id == user_id, Favorite.news_id == news_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def add_favorite(db: AsyncSession, user_id: int, news_id: int):
    favorite = Favorite(user_id=user_id, news_id=news_id)
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)
    return favorite


async def remove_favorite(db: AsyncSession, user_id: int, news_id: int):
    stmt = delete(Favorite).where(Favorite.user_id == user_id, Favorite.news_id == news_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


async def get_favorite_list(db: AsyncSession, user_id: int, page: int, page_size: int):
    offset = (page - 1) * page_size
    count_query = select(func.count()).where(Favorite.user_id == user_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar_one_or_none()

    stmt = select(News, Favorite.created_at.label("favorite_time"), Favorite.id.label("favorite_id")) \
        .join(Favorite, Favorite.news_id == News.id) \
        .where(Favorite.user_id == user_id) \
        .order_by(Favorite.created_at.desc()) \
        .offset(offset).limit(page_size)
    result = await db.execute(stmt)
    return result.all(), total


async def clear_favorite(db: AsyncSession, user_id: int):
    stmt = delete(Favorite).where(Favorite.user_id == user_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount or 0
