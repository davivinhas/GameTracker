from pydantic import BaseModel
from typing import Optional


class MessageResponse(BaseModel):
    message: str


class TrackGameResponse(BaseModel):
    message: str
    game_id: int
    deals_tracked: int


class TrackDealResponse(BaseModel):
    message: str
    game_id: int
    deal_id: int


class RootResponse(BaseModel):
    message: str
    docs: str
    stores: str


class StoreImages(BaseModel):
    banner: str
    logo: str
    icon: str


class StoreResponse(BaseModel):
    storeID: str
    storeName: str
    isActive: int
    images: StoreImages
