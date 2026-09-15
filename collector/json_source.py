import json
from urllib.request import Request, urlopen

from collector.base import BaseCollector, normalize_listing


class JSONCollector(BaseCollector):
    """
    Fetch an existing GitHub Pages JSON endpoint
    and normalize its `items` array.
    """

    def __init__(self, url):
        self.url = url

    def collect(self, search: str):
        request = Request(
            self.url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
            },
        )

        with urlopen(request, timeout=60) as response:
            payload = json.load(response)

        raw_items = payload.get("items", [])
        listings = []

        for item in raw_items:
            normalized = normalize_listing({
                "id": item.get("Listing ID") or item.get("id"),
                "title": item.get("Title") or item.get("title"),
                "brand": item.get("Brand") or item.get("brand"),
                "price_gbp": item.get("Price GBP") or item.get("price_gbp"),
                "likes": item.get("Likes") or item.get("likes") or item.get("like_count"),
                "condition": item.get("Condition") or item.get("condition"),
                "url": item.get("URL") or item.get("url"),
            })

            if normalized["id"]:
                listings.append(normalized)

        return listings
