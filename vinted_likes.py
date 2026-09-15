import sys
sys.stdout.reconfigure(encoding="utf-8")

import os
import csv
import argparse
import re
import requests

API_KEY = os.environ["PARSE_API_KEY"]

ENDPOINT = (
    "https://api.parse.bot/scraper/"
    "4134c107-4d58-43bb-bf6d-24a642f27b69/search_listings"
)


def safe_filename(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


parser = argparse.ArgumentParser(
    description="Find the most-liked Vinted UK listings for a keyword."
)

parser.add_argument(
    "--search",
    default="running t shirt men",
    help="Vinted search keyword"
)

parser.add_argument(
    "--pages",
    type=int,
    default=5,
    help="Number of Vinted result pages to scan"
)

args = parser.parse_args()

SEARCH = args.search
PAGES = args.pages

if PAGES < 1:
    raise ValueError("Pages must be at least 1.")

print(f"Search: {SEARCH}")
print(f"Pages: {PAGES}")
print()

all_items = []

for page in range(1, PAGES + 1):

    print(f"Fetching page {page}...")

    response = requests.get(
        ENDPOINT,
        headers={
            "X-API-Key": API_KEY,
        },
        params={
            "page": page,
            "category_id": 5,
            "search_text": SEARCH,
        },
        timeout=60,
    )

    response.raise_for_status()

    payload = response.json()

    items = payload.get("data", {}).get("items", [])

    print(f"  Found {len(items)} listings")

    all_items.extend(items)


print()
print(f"Fetched {len(all_items)} listings in total.")


# Remove duplicate listings
unique = {}

for item in all_items:

    item_id = item.get("id")

    if item_id:
        unique[item_id] = item


items = list(unique.values())

print(f"Unique listings: {len(items)}")


# Sort by likes
items.sort(
    key=lambda item: item.get("like_count") or 0,
    reverse=True,
)


top_100 = items[:100]


print()
print("TOP 100 BY LIKES")
print("=" * 100)


for rank, item in enumerate(top_100, start=1):

    title = item.get("title") or "Unknown"
    brand = item.get("brand") or "Unknown"
    price = item.get("price_gbp") or "?"
    likes = item.get("like_count") or 0
    condition = item.get("condition") or ""
    url = item.get("url") or ""

    print(
        f"{rank:>3}. "
        f"{title[:50]:50} "
        f"| £{price:<8} "
        f"| Likes {likes:<5}"
    )

    print(f"     {url}")


# Create filename based on search
search_slug = safe_filename(SEARCH)

csv_filename = f"vinted_{search_slug}_top100.csv"


# Save CSV
with open(
    csv_filename,
    "w",
    newline="",
    encoding="utf-8-sig"
) as f:

    writer = csv.writer(f)

    writer.writerow([
        "Rank",
        "Title",
        "Brand",
        "Price GBP",
        "Likes",
        "Condition",
        "URL",
    ])

    for rank, item in enumerate(top_100, start=1):

        writer.writerow([
            rank,
            item.get("title", ""),
            item.get("brand", ""),
            item.get("price_gbp", ""),
            item.get("like_count", 0),
            item.get("condition", ""),
            item.get("url", ""),
        ])


print()
print(f"Saved CSV: {csv_filename}")
