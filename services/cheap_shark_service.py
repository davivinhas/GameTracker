import httpx
from typing import List, Optional, Dict
import time
from schemas.game_data import GameData
from schemas.game_search import GameSearchResponse
import os

CHEAP_SHARK_URL = os.getenv("CHEAP_SHARK_URL")
CHEAP_SHARK_BASE_URL = os.getenv("CHEAP_SHARK_BASE_URL")


class CheapSharkService:
    if not CHEAP_SHARK_BASE_URL:
        raise RuntimeError("CHEAP_SHARK_BASE_URL is not set")

    BASE_URL = CHEAP_SHARK_BASE_URL

    _store_cache: Dict[str, str] = {}
    _store_cache_loaded_at: float = 0.0
    _store_cache_ttl_seconds: int = 60 * 60 * 24

    async def _load_store_cache(self) -> None:
        """Carrega e cacheia o mapeamento storeID -> storeName"""
        now = time.time()
        if self._store_cache and (now - self._store_cache_loaded_at) < self._store_cache_ttl_seconds:
            return

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/stores")
            stores = response.json()

        self._store_cache = {s["storeID"]: s["storeName"] for s in stores}
        self._store_cache_loaded_at = now

    async def _get_store_name(self, store_id: Optional[str]) -> Optional[str]:
        if not store_id:
            return None
        await self._load_store_cache()
        return self._store_cache.get(store_id)

    async def get_stores(self) -> List[Dict]:
        """Lista todas as stores disponíveis"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/stores")
            return response.json()

    async def search_games(self, title: str, limit: int = 10) -> List[GameSearchResponse]:
        """Busca jogos por título"""
        async with httpx.AsyncClient() as client:
            params = {"title": title, "limit": limit}
            response = await client.get(f"{self.BASE_URL}/games", params=params)
            games = response.json()

            result = []
            for game in games:
                cheapest_price = float(game.get("cheapest", 0))
                result.append(GameSearchResponse(
                    title=game["external"],
                    game_id=game.get("gameID"),
                    deal_id=game.get("cheapestDealID"),
                    price=cheapest_price,
                    discount_percentage=0.0,
                    url=f"{CHEAP_SHARK_URL}{game.get('cheapestDealID')}" if CHEAP_SHARK_URL else None,
                    image_url=game.get("thumb"),
                    is_on_sale=False
                ))

            return result

    async def get_deals(
            self,
            store_id: Optional[str] = None,
            min_discount: int = 0,
            max_price: Optional[float] = None,
            limit: int = 60
    ) -> List[GameData]:
        """Obtém deals/promoções"""
        async with httpx.AsyncClient() as client:
            params = {
                "pageSize": limit,
                "lowerPrice": 0,
            }

            if store_id:
                params["storeID"] = store_id
            if max_price:
                params["upperPrice"] = max_price
            if min_discount > 0:
                params["onSale"] = 1

            response = await client.get(f"{self.BASE_URL}/deals", params=params)
            deals = response.json()

            result = []
            for deal in deals:
                sale_price = float(deal["salePrice"])
                normal_price = float(deal["normalPrice"])
                savings = float(deal["savings"])
                store_id = deal["storeID"]

                # Filtrar por desconto mínimo
                if savings < min_discount:
                    continue

                store_name = await self._get_store_name(store_id)
                result.append(GameData(
                    title=deal["title"],
                    deal_id=deal["dealID"],
                    store_id=store_id,
                    store_name=store_name or f"Store {store_id}",
                    price=sale_price,
                    original_price=normal_price,
                    discount_percentage=round(savings, 2),
                    url=f"{CHEAP_SHARK_URL}{deal['dealID']}" if CHEAP_SHARK_URL else None,
                    image_url=deal.get("thumb"),
                    is_on_sale=True
                ))

            return result

    async def get_game_details(self, game_id: str) -> Optional[GameData]:
        """Obtém detalhes de um jogo específico"""
        async with httpx.AsyncClient() as client:
            params = {"id": game_id}
            response = await client.get(f"{self.BASE_URL}/games", params=params)

            if response.status_code != 200:
                return None

            data = response.json()

            if not data.get("deals"):
                return None

            # Pega o melhor deal
            best_deal = min(data["deals"], key=lambda x: float(x["price"]))

            sale_price = float(best_deal["price"])
            retail_price = float(best_deal["retailPrice"])
            savings = float(best_deal["savings"])

            store_name = await self._get_store_name(best_deal["storeID"])
            return GameData(
                title=data["info"]["title"],
                game_id=game_id,
                deal_id=best_deal["dealID"],
                store_id=best_deal["storeID"],
                store_name=store_name or "Unknown",
                price=sale_price,
                original_price=retail_price,
                discount_percentage=round(savings, 2),
                url=f"{CHEAP_SHARK_URL}{best_deal['dealID']}" if CHEAP_SHARK_URL else None,
                image_url=data["info"].get("thumb"),
                is_on_sale=savings > 0
            )

    async def get_game_deals(self, game_id: str) -> Optional[Dict]:
        """Obtém todas as ofertas (deals) de um jogo"""
        async with httpx.AsyncClient() as client:
            params = {"id": game_id}
            response = await client.get(f"{self.BASE_URL}/games", params=params)

            if response.status_code != 200:
                return None

            data = response.json()

            if not data.get("deals"):
                return None

            title = data["info"]["title"]
            image_url = data["info"].get("thumb")
            deals = []
            for deal in data["deals"]:
                sale_price = float(deal["price"])
                retail_price = float(deal.get("retailPrice", sale_price))
                savings = float(deal.get("savings", 0))
                store_id = deal.get("storeID")
                deal_id = deal.get("dealID")

                store_name = await self._get_store_name(store_id)
                deals.append(GameData(
                    title=title,
                    game_id=game_id,
                    deal_id=deal_id,
                    store_id=store_id,
                    store_name=store_name or (f"Store {store_id}" if store_id else None),
                    price=sale_price,
                    original_price=retail_price,
                    discount_percentage=round(savings, 2),
                    url=f"{CHEAP_SHARK_URL}{deal_id}" if (CHEAP_SHARK_URL and deal_id) else None,
                    image_url=image_url,
                    is_on_sale=savings > 0
                ))

            return {"title": title, "image_url": image_url, "deals": deals}

    async def get_deal_by_id(self, deal_id: str) -> Optional[GameData]:
        """Obtém detalhes de um deal específico"""
        async with httpx.AsyncClient() as client:
            params = {"id": deal_id}
            response = await client.get(f"{self.BASE_URL}/deals", params=params)

            if response.status_code != 200:
                return None

            deal = response.json()

            sale_price = float(deal["gameInfo"]["salePrice"])
            retail_price = float(deal["gameInfo"]["retailPrice"])
            savings = ((retail_price - sale_price) / retail_price * 100) if retail_price > 0 else 0

            store_name = await self._get_store_name(deal["gameInfo"].get("storeID"))
            return GameData(
                title=deal["gameInfo"]["name"],
                game_id=deal["gameInfo"].get("gameID"),
                deal_id=deal_id,
                store_id=deal["gameInfo"].get("storeID"),
                store_name=store_name or "Unknown",
                price=sale_price,
                original_price=retail_price,
                discount_percentage=round(savings, 2),
                url=f"{CHEAP_SHARK_URL}{deal_id}" if CHEAP_SHARK_URL else None,
                image_url=deal["gameInfo"].get("thumb"),
                is_on_sale=savings > 0
            )
