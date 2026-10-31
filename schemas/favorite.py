from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from schemas.base import NewsItemBase


class FavoriteCheckResponse(BaseModel):
    is_favorite: bool = Field(..., alias="isFavorite")


class FavoriteAllRequest(BaseModel):
    news_id: int = Field(..., alias="newsId")


class FavoriteNewsItemRequest(NewsItemBase):
    favorite_id: int = Field(alias="favoriteId")
    favorite_time: datetime = Field(alias="favoriteTime")
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )


class FavoriteListResponse(BaseModel):
    list: list[FavoriteNewsItemRequest]
    total: int
    has_more: bool = Field(alias="hasMore")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )
