from abc import ABC, abstractmethod


class BaseCollector(ABC):
    """
    Base interface for all collectors.

    Every collector should return a list of normalized
    listing dictionaries.
    """

    @abstractmethod
    def collect(self, search: str):
        raise NotImplementedError


def normalize_listing(item):
    """
    Convert data from any source into one common format.
    """

    listing_id = (
        item.get("id")
        or item.get("listing_id")
        or item.get("Listing ID")
        or item.get("url")
        or item.get("URL")
        or ""
    )

    title = (
        item.get("title")
        or item.get("Title")
        or ""
    )

    brand = (
        item.get("brand")
        or item.get("Brand")
        or ""
    )

    price = (
        item.get("price_gbp")
        or item.get("Price GBP")
        or item.get("price")
        or item.get("Price")
        or ""
    )

    likes_raw = (
        item.get("likes")
        or item.get("Likes")
        or item.get("like_count")
        or 0
    )

    try:
        likes = int(float(likes_raw))
    except (ValueError, TypeError):
        likes = 0

    condition = (
        item.get("condition")
        or item.get("Condition")
        or ""
    )

    url = (
        item.get("url")
        or item.get("URL")
        or ""
    )

    return {
        "id": str(listing_id),
        "title": str(title),
        "brand": str(brand),
        "price_gbp": price,
        "likes": likes,
        "condition": str(condition),
        "url": str(url),
    }
