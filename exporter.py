"""
exporter.py

Exports the current radar snapshot (list of detected devices) to a
timestamped CSV or JSON file in an `exports/` folder next to this
script.
"""

import csv
import json
import time
from pathlib import Path
from typing import List, Dict

EXPORT_DIR = Path(__file__).parent / "exports"


def _ensure_dir():
    EXPORT_DIR.mkdir(exist_ok=True)


def export_csv(devices: List[Dict]) -> Path:
    _ensure_dir()
    filename = EXPORT_DIR / f"scan_{time.strftime('%Y%m%d_%H%M%S')}.csv"
    fieldnames = ["name", "kind", "address", "rssi", "vendor",
                  "distance_m", "times_seen", "first_seen_today"]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for d in devices:
            writer.writerow(d)

    return filename


def export_json(devices: List[Dict]) -> Path:
    _ensure_dir()
    filename = EXPORT_DIR / f"scan_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(devices, f, indent=2, default=str)
    return filename


if __name__ == "__main__":
    sample = [
        {"name": "Test Phone", "kind": "BLE", "address": "AA:BB:CC:11:22:33",
         "rssi": -55, "vendor": "Apple", "distance_m": 3.2,
         "times_seen": 4, "first_seen_today": True}
    ]
    print(export_csv(sample))
    print(export_json(sample))
