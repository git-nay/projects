import argparse
import csv
import re
from datetime import datetime, timezone
from pathlib import Path

from collector.csv_source import CSVCollector
from collector.json_source import JSONCollector


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def read_previous_latest(path):
    previous = {}

    if not path.exists():
        return previous

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:
            listing_id = (
                row.get("Listing ID")
                or row.get("URL")
            )

            if not listing_id:
                continue

            try:
                likes = int(
                    float(row.get("Likes") or 0)
                )
            except ValueError:
                likes = 0

            try:
                rank = int(
                    row.get("Rank") or 0
                )
            except ValueError:
                rank = 0

            previous[str(listing_id)] = {
                "likes": likes,
                "rank": rank,
            }

    return previous


parser = argparse.ArgumentParser(
    description="Source-agnostic Vinted trend pipeline."
)

parser.add_argument(
    "--source",
    choices=["csv", "json"],
    default="json"
)

parser.add_argument(
    "--input",
    required=True,
    help="CSV path or JSON URL"
)

parser.add_argument(
    "--search",
    required=True,
    help="Keyword this dataset represents"
)

parser.add_argument(
    "--top",
    type=int,
    default=100
)

args = parser.parse_args()


search_slug = slugify(
    args.search
)

latest_dir = Path(
    "results/latest"
)

history_dir = (
    Path("results/history")
    / search_slug
)

latest_dir.mkdir(
    parents=True,
    exist_ok=True
)

history_dir.mkdir(
    parents=True,
    exist_ok=True
)


latest_file = (
    latest_dir
    / f"{search_slug}.csv"
)


previous = read_previous_latest(
    latest_file
)


if args.source == "json":

    collector = JSONCollector(
        args.input
    )

else:

    collector = CSVCollector(
        args.input
    )


items = collector.collect(
    args.search
)


# Remove duplicates
unique = {}

for item in items:
    unique[item["id"]] = item

items = list(
    unique.values()
)


# Sort highest likes first
items.sort(
    key=lambda item: item["likes"],
    reverse=True
)


rows = []


for rank, item in enumerate(
    items,
    start=1
):

    old = previous.get(
        item["id"]
    )

    if old:

        previous_likes = (
            old["likes"]
        )

        previous_rank = (
            old["rank"]
        )

        likes_gained = (
            item["likes"]
            - previous_likes
        )

        rank_change = (
            previous_rank
            - rank
        )

        if previous_likes > 0:

            likes_gained_pct = round(
                likes_gained
                / previous_likes
                * 100,
                1
            )

        else:
            likes_gained_pct = ""

        is_new = "No"

    else:

        previous_likes = ""
        previous_rank = ""
        likes_gained = ""
        likes_gained_pct = ""
        rank_change = ""
        is_new = "Yes"


    rows.append({
        "Rank": rank,
        "Listing ID": item["id"],
        "Title": item["title"],
        "Brand": item["brand"],
        "Price GBP": item["price_gbp"],
        "Likes": item["likes"],
        "Previous Likes": previous_likes,
        "Likes Gained": likes_gained,
        "Likes Gained %": likes_gained_pct,
        "Previous Rank": previous_rank,
        "Rank Change": rank_change,
        "New Listing": is_new,
        "Condition": item["condition"],
        "URL": item["url"],
    })


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


timestamp = datetime.now(
    timezone.utc
).strftime(
    "%Y-%m-%d_%H%M%S"
)


history_file = (
    history_dir
    / f"{timestamp}.csv"
)


# Save all collected rows historically
with history_file.open(
    "w",
    encoding="utf-8-sig",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(rows)


# Save Top N as latest
with latest_file.open(
    "w",
    encoding="utf-8-sig",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()

    writer.writerows(
        rows[:args.top]
    )


print(
    f"Imported: {len(items)} unique listings"
)

print(
    f"History: {history_file}"
)

print(
    f"Latest Top {args.top}: {latest_file}"
)
