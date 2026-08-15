"""
device_db.py

Local SQLite storage for scan history. This is what powers:
  - "NEW" vs "seen before, Nx" tagging
  - Per-device RSSI-over-time history (for the mini graph)
  - A persistent record of what's been detected across sessions

Everything is stored in a local file `radar_history.db` next to this
script. Nothing is sent anywhere — it's a plain local log, the same
idea as your router's own "connected devices" history page.
"""

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

DB_PATH = Path(__file__).parent / "radar_history.db"


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sightings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT NOT NULL,
            name TEXT,
            kind TEXT,
            rssi INTEGER,
            vendor TEXT,
            timestamp REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_address ON sightings(address)
    """)
    return conn


@dataclass
class DeviceStats:
    first_seen: float
    last_seen: float
    total_sightings: int
    is_new_today: bool


def record_sighting(address: str, name: str, kind: str, rssi: int, vendor: str = ""):
    conn = _connect()
    with conn:
        conn.execute(
            "INSERT INTO sightings (address, name, kind, rssi, vendor, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (address, name, kind, rssi, vendor, time.time()),
        )
    conn.close()


def get_device_stats(address: str) -> Optional[DeviceStats]:
    conn = _connect()
    cur = conn.execute(
        "SELECT MIN(timestamp), MAX(timestamp), COUNT(*) FROM sightings "
        "WHERE address = ?",
        (address,),
    )
    row = cur.fetchone()
    conn.close()

    if row is None or row[2] == 0:
        return None

    first_seen, last_seen, total = row
    is_new_today = (time.time() - first_seen) < 86400
    return DeviceStats(first_seen=first_seen, last_seen=last_seen,
                        total_sightings=total, is_new_today=is_new_today)


def get_rssi_history(address: str, limit: int = 30) -> List[float]:
    """Most recent RSSI readings for a device, oldest first."""
    conn = _connect()
    cur = conn.execute(
        "SELECT rssi FROM sightings WHERE address = ? "
        "ORDER BY timestamp DESC LIMIT ?",
        (address, limit),
    )
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return list(reversed(rows))


def get_all_known_addresses() -> List[str]:
    conn = _connect()
    cur = conn.execute("SELECT DISTINCT address FROM sightings")
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows


def prune_old_history(max_age_days: int = 30):
    """Optional housekeeping: delete sightings older than max_age_days."""
    cutoff = time.time() - (max_age_days * 86400)
    conn = _connect()
    with conn:
        conn.execute("DELETE FROM sightings WHERE timestamp < ?", (cutoff,))
    conn.close()


if __name__ == "__main__":
    # quick smoke test
    record_sighting("AA:BB:CC:11:22:33", "Test Device", "BLE", -55, "Apple")
    stats = get_device_stats("AA:BB:CC:11:22:33")
    print(stats)
    print(get_rssi_history("AA:BB:CC:11:22:33"))
