import sys
sys.stdout.reconfigure(encoding="utf-8")

import os
import csv
import requests

API_KEY = os.environ["PARSE_API_KEY"]

ENDPOINT = (
    "https://api.parse.bot/scraper/"
    "4134c107-4d58-43bb-bf6d-24a642f27b69/search_listings"
)

SEARCH = "running t shirt men"
PAGES = 5

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
        timeout=30,
    )

    response.raise_for_status()

    payload = response.json()
    items = payload["data"]["items"]

    all_items.extend(items)

print(f"\nFetched {len(all_items)} listings.")

# Remove duplicate listings
unique = {
    item["id"]: item
    for item in all_items
    if item.get("id")
}

items = list(unique.values())

# Sort highest likes first
items.sort(
    key=lambda item: item.get("like_count") or 0,
    reverse=True,
)

top_100 = items[:100]

print("\nTOP 100 BY LIKES\n")
print("=" * 100)

for rank, item in enumerate(top_100, start=1):
    title = item.get("title", "Unknown")
    brand = item.get("brand") or "Unknown"
    price = item.get("price_gbp") or "?"
    likes = item.get("like_count") or 0
    condition = item.get("condition") or ""
    url = item.get("url") or ""

    print(
        f"{rank:>3}. "
        f"{title[:45]:45} "
        f"| {brand[:18]:18} "
        f"| £{price:<8} "
        f"| Likes {likes:<5} "
        f"| {condition}"
    )

    print(f"     {url}")


# Save results to CSV
csv_filename = "vinted_top_100.csv"

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

print(f"\nSaved CSV: {csv_filename}")
