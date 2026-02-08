# services/cheapshark_service.py
import httpx
from typing import List, Optional, Dict
from schemas.cheak_shark import CheapSharkDeal
from schemas.game_data import GameData
import os

CHEAP_SHARK_URL = os.getenv("CHEAP_SHARK_URL")

class CheapSharkService:
    BASE_URL = os.getenv("CHEAP_SHARK_BASE_URL")

    # Mapeamento de store IDs para nomes
    STORES = {
        "1": "Steam",
        "2": "GamersGate",
        "3": "GreenManGaming",
        "7": "GOG",
        "8": "Origin",
        "11": "Humble Store",
        "13": "Uplay",
        "15": "Fanatical",
        "25": "Epic Games Store",
        "27": "Gamesplanet",
        "28": "Voidu",
        "29": "Epic Games Store",
        "30": "GameBillet",
    }

    async def get_stores(self) -> List[Dict]:
        """Lista todas as stores disponíveis"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/stores")
            return response.json()

    async def search_games(self, title: str, limit: int = 10) -> List[GameData]:
        """Busca jogos por título"""
        async with httpx.AsyncClient() as client:
            params = {"title": title, "limit": limit}
            response = await client.get(f"{self.BASE_URL}/games", params=params)
            games = response.json()

            result = []
            for game in games:
                # Pega o melhor deal do jogo
                cheapest_price = float(game.get("cheapest", 0))
                normal_price = float(game.get("normalPrice", cheapest_price))
                savings = float(game.get("cheapestDealID", "0"))

                result.append(GameData(
                    title=game["external"],
                    platform="Multiple",  # CheapShark agrega várias stores
                    external_id=game["gameID"],
                    price=cheapest_price,
                    original_price=normal_price if cheapest_price < normal_price else None,
                    discount_percentage=round((1 - cheapest_price / normal_price) * 100, 2) if normal_price > 0 else 0,
                    url=f"{CHEAP_SHARK_URL}{game.get('cheapestDealID')}",
                    image_url=game.get("thumb"),
                    is_on_sale=cheapest_price < normal_price
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

                result.append(GameData(
                    title=deal["title"],
                    platform=self.STORES.get(store_id, f"Store {store_id}"),
                    external_id=deal["dealID"],
                    price=sale_price,
                    original_price=normal_price,
                    discount_percentage=round(savings, 2),
                    url=f"{CHEAP_SHARK_URL}{deal['dealID']}",
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

            return GameData(
                title=data["info"]["title"],
                platform=self.STORES.get(best_deal["storeID"], "Unknown"),
                external_id=best_deal["dealID"],
                price=sale_price,
                original_price=retail_price,
                discount_percentage=round(savings, 2),
                url=f"{CHEAP_SHARK_URL}{best_deal['dealID']}",
                image_url=data["info"].get("thumb"),
                is_on_sale=savings > 0
            )

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

            return GameData(
                title=deal["gameInfo"]["name"],
                platform=self.STORES.get(deal["gameInfo"]["storeID"], "Unknown"),
                external_id=deal_id,
                price=sale_price,
                original_price=retail_price,
                discount_percentage=round(savings, 2),
                url=f"{CHEAP_SHARK_URL}{deal_id}",
                image_url=deal["gameInfo"].get("thumb"),
                is_on_sale=savings > 0
            )