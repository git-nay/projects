import csv
import json
from pathlib import Path

RESULTS = Path("results")
LATEST = RESULTS / "latest"

SITE = Path("site")
API = SITE / "api"
SEARCH_API = API / "search"

SEARCH_API.mkdir(parents=True, exist_ok=True)


def convert_value(value):
    if value is None:
        return None

    value = value.strip()

    if value == "":
        return None

    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        pass

    return value


keywords = []

if LATEST.exists():

    for csv_file in sorted(LATEST.glob("*.csv")):

        slug = csv_file.stem

        print(f"Building API: {slug}")

        rows = []

        with csv_file.open(
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as f:

            reader = csv.DictReader(f)

            for row in reader:

                clean_row = {
                    key: convert_value(value)
                    for key, value in row.items()
                }

                rows.append(clean_row)

        output = {
            "keyword": slug.replace("_", " "),
            "slug": slug,
            "count": len(rows),
            "items": rows
        }

        json_file = SEARCH_API / f"{slug}.json"

        with json_file.open(
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                output,
                f,
                ensure_ascii=False,
                indent=2
            )

        keywords.append({
            "keyword": slug.replace("_", " "),
            "slug": slug,
            "count": len(rows),
            "endpoint": f"api/search/{slug}.json"
        })


with (API / "keywords.json").open(
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        {
            "keywords": keywords
        },
        f,
        ensure_ascii=False,
        indent=2
    )


print()
print(f"Built {len(keywords)} keyword APIs.")
