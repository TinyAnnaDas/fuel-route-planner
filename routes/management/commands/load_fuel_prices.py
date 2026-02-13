import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.management.base import BaseCommand

from routes.models import FuelStation

BATCH_SIZE = 1000
CSV_PATH = Path(__file__).resolve().parent.parent.parent / "data/fuel-prices.csv"

def strip(val):
    return val.strip() if isinstance(val, str) else val

def parse_price(val):
    if val is None:
        return None

    if isinstance(val, str):
        val = val.strip()
        if not val:
            return None

    try:
        return Decimal(val)
    except (InvalidOperation, TypeError):
        return None


class Command(BaseCommand):
    help = "Load fuel prices from CSV into Fuel Station table"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action = "store_true",
            help = "Delete existing Fuel Station rows before loading."
        )
    def handle(self, *args, **options):
        self.stdout.write("Load started.")
        self.stdout.write(f"CSV path: {CSV_PATH}")
        self.stdout.write(f"Exists: {CSV_PATH.exists()}")
        if not CSV_PATH.exists():
            self.stderr.write(self.style.ERROR(f"CSV not found: {CSV_PATH}"))
            return
        if options["clear"]:
            deleted, _ = FuelStation.objects.all().delete()
            self.stdout.write(f"Cleared {deleted} existing rows.")

        rows = []
        skipped = 0
        with open(CSV_PATH, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                price = parse_price(row.get("Retail Price"))
                if price is None:
                    skipped +=1
                    continue
                try:
                    rack_id = int(row.get("Rack ID") or 0)
                    opis_id = int(row.get("OPIS Truckstop ID") or 0)
                except (TypeError, ValueError):
                    skipped +=1
                    continue
                rows.append(
                    FuelStation(
                    opis_truck_stop_id = opis_id,
                    truck_stop_name = strip(row.get("Truckstop Name", ""))[:255],
                    address = strip(row.get("Address", ""))[:255],
                    city=strip(row.get("City", ""))[:100],
                    state=strip(row.get("State", ""))[:2],
                    rack_id = rack_id,
                    retail_price = price,
                    )
                )

                if len(rows) >= BATCH_SIZE:
                    FuelStation.objects.bulk_create(rows)
                    self.stdout.write(f"Inserted {len(rows)} rows...")
                    rows = []
        if rows:
            FuelStation.objects.bulk_create(rows)
            total = FuelStation.objects.count()
            self.stdout.write(self.style.SUCCESS(f"Done. Total FuelStation rows: {total}. Skipped: {skipped}."))

