import csv
from pathlib import Path

from collector.base import BaseCollector, normalize_listing


class CSVCollector(BaseCollector):
    """
    Read Vinted listing data from a CSV file.

    Accepted column names include:

    Listing ID / id
    Title / title
    Brand / brand
    Price GBP / price_gbp / price
    Likes / likes / like_count
    Condition / condition
    URL / url
    """

    def __init__(self, csv_path):
        self.csv_path = Path(csv_path)

    @staticmethod
    def _lower_keys(row):
        """
        Convert CSV header names to lowercase
        so column matching is more flexible.
        """

        return {
            str(key).strip().lower(): value
            for key, value in row.items()
            if key is not None
        }

    @staticmethod
    def _first(row, *names):
        """
        Return the first non-empty matching field.
        """

        for name in names:
            value = row.get(
                name.lower()
            )

            if value not in (
                None,
                ""
            ):
                return value

        return ""

    def collect(self, search: str):
        """
        Load and normalize all listings from the CSV.
        """

        if not self.csv_path.exists():
            raise FileNotFoundError(
                f"Input CSV not found: {self.csv_path}"
            )

        listings = []

        with self.csv_path.open(
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as f:

            reader = csv.DictReader(f)

            for raw_row in reader:

                row = self._lower_keys(
                    raw_row
                )

                item = {
                    "id": self._first(
                        row,
                        "listing id",
                        "id"
                    ),

                    "title": self._first(
                        row,
                        "title"
                    ),

                    "brand": self._first(
                        row,
                        "brand"
                    ),

                    "price_gbp": self._first(
                        row,
                        "price gbp",
                        "price_gbp",
                        "price"
                    ),

                    "likes": self._first(
                        row,
                        "likes",
                        "like_count"
                    ),

                    "condition": self._first(
                        row,
                        "condition"
                    ),

                    "url": self._first(
                        row,
                        "url"
                    ),
                }

                normalized = normalize_listing(
                    item
                )

                if normalized["id"]:
                    listings.append(
                        normalized
                    )

        return listings
