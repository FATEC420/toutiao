from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from models.news import Category, News
from news_cache import get_cached_categories, set_cache_categories, get_cache_news_list, set_cache_news_list
from schemas.base import NewsItemBase


# async def get_categories(db: AsyncSession, skip: int = 0, limit: int = 100):
#     stmt = select(Category).offset(skip).limit(limit)
#     result = await db.execute(stmt)
#     return result.scalars().all()

async def get_categories(db: AsyncSession, skip: int = 0, limit: int = 100):
    # 尝试从缓存获取
    cached_categories = await get_cached_categories()

    if cached_categories:
        return cached_categories

    # 如果缓存没有，则从数据库中查询
    stmt = select(Category).offset(skip).limit(limit)
    result = await db.execute(stmt)
    categories = result.scalars().all()

    # 缓存新闻分类列表
    if categories:
        categories = jsonable_encoder(categories)
        await set_cache_categories(categories)

    return categories


async def get_news_list(db: AsyncSession, category_id: int, skip: int = 0, limit: int = 100):
    page = skip // limit + 1
    cached_news_list = await get_cache_news_list(category_id, page, limit)
    if cached_news_list:
        return [News(**item) for item in cached_news_list]

    stmt = select(News).where(News.category_id == category_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    news_list = result.scalars().all()

    if news_list:
        news_list = [NewsItemBase.model_validate(item).model_dump(mode="json", by_alias=False) for item in news_list]
        await set_cache_news_list(category_id, page, limit, news_list)

    return news_list


async def get_news_count(db: AsyncSession, category_id: int):
    stmt = select(func.count(News.id)).where(News.category_id == category_id)
    result = await db.execute(stmt)
    return result.scalar_one()


async def get_news_detail(db: AsyncSession, news_id: int):
    stmt = select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def increase_news_views(db: AsyncSession, news_id: int):
    stmt = update(News).where(News.id == news_id).values(views=News.views + 1)
    result = await db.execute(stmt)
    await db.commit()
    # 更新 -》 检查数据库是否真的命中数据
    return result.rowcount > 0


async def get_related_news(db: AsyncSession, news_id: int, category_id: int, limit: int = 5):
    stmt = select(News) \
        .where(News.category_id == category_id, News.id != news_id) \
        .order_by(News.views.desc(), News.publish_time.desc()).limit(limit)
    result = await db.execute(stmt)

    related_news = result.scalars().all()
    # 列表推导式，推导出新闻的核心数据
    return [{"id": news.id,
             "title": news.title,
             "content": news.content,
             "image": news.image,
             "author": news.author,
             "category_id": news.category_id,
             "views": news.views,
             "publish_time": news.publish_time} for news in related_news]
    # return result.scalars().all()
