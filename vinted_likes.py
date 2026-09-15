import sys
sys.stdout.reconfigure(encoding="utf-8")

import os
import csv
import argparse
import re
from datetime import datetime, timezone
from pathlib import Path

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


def get_listing_key(item):
    """
    Prefer Vinted item ID.
    Fall back to URL if ID is unavailable.
    """
    return str(item.get("id") or item.get("url") or "")


def load_previous_snapshot(history_folder):
    """
    Loads the newest existing CSV for this search,
    before the current run creates a new one.
    """

    history_folder = Path(history_folder)

    if not history_folder.exists():
        return {}

    csv_files = sorted(history_folder.glob("*.csv"))

    if not csv_files:
        return {}

    previous_file = csv_files[-1]

    print(f"Previous snapshot: {previous_file}")

    previous = {}

    with open(
        previous_file,
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            listing_id = row.get("Listing ID") or row.get("URL")

            if not listing_id:
                continue

            try:
                likes = int(float(row.get("Likes", 0) or 0))
            except ValueError:
                likes = 0

            try:
                rank = int(row.get("Rank", 0) or 0)
            except ValueError:
                rank = 0

            previous[str(listing_id)] = {
                "likes": likes,
                "rank": rank,
            }

    return previous


parser = argparse.ArgumentParser(
    description="Track most-liked Vinted UK listings."
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
    help="Number of result pages to scan"
)

args = parser.parse_args()

SEARCH = args.search
PAGES = args.pages

if PAGES < 1:
    raise ValueError("Pages must be at least 1.")


search_slug = safe_filename(SEARCH)

history_folder = Path(
    "results",
    "history",
    search_slug
)

latest_folder = Path(
    "results",
    "latest"
)

history_folder.mkdir(
    parents=True,
    exist_ok=True
)

latest_folder.mkdir(
    parents=True,
    exist_ok=True
)


# Load previous data BEFORE creating today's snapshot
previous_data = load_previous_snapshot(
    history_folder
)


print()
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

    items = payload.get(
        "data",
        {}
    ).get(
        "items",
        []
    )

    print(
        f"  Found {len(items)} listings"
    )

    all_items.extend(items)


print()
print(
    f"Fetched {len(all_items)} listings."
)


# Remove duplicates
unique = {}

for item in all_items:

    key = get_listing_key(item)

    if key:
        unique[key] = item


items = list(unique.values())

print(
    f"Unique listings: {len(items)}"
)


# Sort by current likes
items.sort(
    key=lambda item: (
        item.get("like_count") or 0
    ),
    reverse=True,
)


top_100 = items[:100]


# Add trend calculations
rows = []

for rank, item in enumerate(
    top_100,
    start=1
):

    listing_id = get_listing_key(item)

    current_likes = (
        item.get("like_count") or 0
    )

    previous = previous_data.get(
        listing_id
    )

    if previous:

        previous_likes = previous["likes"]
        previous_rank = previous["rank"]

        likes_gained = (
            current_likes
            - previous_likes
        )

        if previous_likes > 0:
            likes_gain_percent = round(
                (
                    likes_gained
                    / previous_likes
                ) * 100,
                1
            )
        else:
            likes_gain_percent = ""

        # Positive number = moved UP ranking
        rank_change = (
            previous_rank - rank
        )

        new_listing = "No"

    else:

        previous_likes = ""
        previous_rank = ""
        likes_gained = ""
        likes_gain_percent = ""
        rank_change = ""
        new_listing = "Yes"


    rows.append({
        "Rank": rank,
        "Listing ID": listing_id,
        "Title": item.get(
            "title",
            ""
        ),
        "Brand": item.get(
            "brand",
            ""
        ),
        "Price GBP": item.get(
            "price_gbp",
            ""
        ),
        "Likes": current_likes,
        "Previous Likes": previous_likes,
        "Likes Gained": likes_gained,
        "Likes Gained %": likes_gain_percent,
        "Previous Rank": previous_rank,
        "Rank Change": rank_change,
        "New Listing": new_listing,
        "Condition": item.get(
            "condition",
            ""
        ),
        "URL": item.get(
            "url",
            ""
        ),
    })


print()
print("TOP 100 BY LIKES")
print("=" * 110)

for row in rows:

    gain = row["Likes Gained"]

    if gain == "":
        gain_display = "NEW"
    elif gain > 0:
        gain_display = f"+{gain}"
    else:
        gain_display = str(gain)

    print(
        f'{row["Rank"]:>3}. '
        f'{row["Title"][:48]:48} '
        f'| £{str(row["Price GBP"]):<7} '
        f'| Likes {row["Likes"]:<4} '
        f'| Gain {gain_display}'
    )


# UTC timestamp keeps GitHub runs consistent
timestamp = datetime.now(
    timezone.utc
).strftime(
    "%Y-%m-%d_%H%M"
)


history_filename = (
    history_folder
    / f"{timestamp}.csv"
)

latest_filename = (
    latest_folder
    / f"{search_slug}.csv"
)


fieldnames = [
    "Rank",
    "Listing ID",
    "Title",
    "Brand",
    "Price GBP",
    "Likes",
    "Previous Likes",
    "Likes Gained",
    "Likes Gained %",
    "Previous Rank",
    "Rank Change",
    "New Listing",
    "Condition",
    "URL",
]


def write_csv(filename):

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(rows)


write_csv(history_filename)

write_csv(latest_filename)


print()
print(
    f"Historical snapshot saved: "
    f"{history_filename}"
)

print(
    f"Latest results saved: "
    f"{latest_filename}"
)
