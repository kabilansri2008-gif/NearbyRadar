"""
oui_lookup.py

Offline manufacturer lookup from a MAC address / BSSID prefix (OUI —
Organizationally Unique Identifier). The first 3 octets of a MAC
address are assigned to a manufacturer by the IEEE, so we can tell
you "this is an Apple device" or "this is a Samsung device" without
any network request and without revealing anything about the actual
owner.

This ships with a small built-in table covering the most common
consumer device vendors. For a full lookup you can optionally point
it at a downloaded IEEE OUI CSV (https://standards-oui.ieee.org/) —
see `load_external_oui_csv()`.
"""

import re
from typing import Optional

# Small built-in table of common consumer-device vendor OUI prefixes.
# Format: "AA:BB:CC" (uppercase, colon-separated) -> vendor name
_BUILTIN_OUI = {
    "00:1B:63": "Apple",
    "00:CD:FE": "Apple",
    "04:0C:CE": "Apple",
    "3C:15:C2": "Apple",
    "A4:C3:61": "Apple",
    "AC:87:A3": "Apple",
    "D0:03:4B": "Apple",
    "F0:18:98": "Apple",
    "F4:0F:24": "Apple",
    "00:16:6C": "Samsung",
    "00:26:37": "Samsung",
    "08:D4:2B": "Samsung",
    "1C:5A:3E": "Samsung",
    "34:BE:00": "Samsung",
    "5C:0A:5B": "Samsung",
    "8C:71:F8": "Samsung",
    "E8:50:8B": "Samsung",
    "00:1A:11": "Google",
    "3C:5A:B4": "Google",
    "54:60:09": "Google",
    "F4:F5:D8": "Google",
    "A4:77:33": "Xiaomi",
    "64:B4:73": "Xiaomi",
    "68:DF:DD": "Xiaomi",
    "8C:BE:BE": "Xiaomi",
    "00:0C:E7": "Huawei",
    "00:E0:FC": "Huawei",
    "20:F3:A3": "Huawei",
    "4C:1F:CC": "Huawei",
    "AC:E2:15": "Sony",
    "FC:0F:E6": "Sony",
    "00:1D:0F": "Amazon",
    "34:D2:70": "Amazon",
    "68:37:E9": "Amazon",
    "F0:81:73": "Amazon",
    "00:1C:B3": "Microsoft",
    "28:18:78": "Microsoft",
    "60:45:BD": "Microsoft",
    "AC:22:0B": "Nintendo",
    "CC:FB:65": "Nintendo",
    "E0:E7:51": "Nintendo",
    "88:C6:26": "Fitbit",
    "AC:37:43": "Garmin",
    "00:19:70": "Garmin",
    "88:0F:10": "Bose",
    "00:0C:8A": "Bose",
    "38:18:4C": "JBL / Harman",
    "AC:BC:32": "Dell",
    "F8:BC:12": "Dell",
}

_external_table: dict = {}


def load_external_oui_csv(path: str) -> int:
    """
    Optionally load a full IEEE OUI CSV file (columns: Assignment,
    Organization Name, ...). Download from:
    https://standards-oui.ieee.org/oui/oui.csv

    Returns the number of entries loaded.
    """
    global _external_table
    count = 0
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                parts = line.split(",")
                if len(parts) < 3:
                    continue
                raw_prefix = parts[1].strip().upper()
                org = parts[2].strip().strip('"')
                if len(raw_prefix) == 6 and re.match(r"^[0-9A-F]{6}$", raw_prefix):
                    prefix = f"{raw_prefix[0:2]}:{raw_prefix[2:4]}:{raw_prefix[4:6]}"
                    _external_table[prefix] = org
                    count += 1
    except FileNotFoundError:
        pass
    return count


def lookup_vendor(mac_or_bssid: Optional[str]) -> str:
    """
    Look up the manufacturer for a MAC address / BSSID.
    Returns "Unknown" if not found, address is malformed, or the
    address is empty (e.g. a randomized/private BLE address, which
    modern phones use by default specifically to prevent this kind
    of tracking).
    """
    if not mac_or_bssid:
        return "Unknown"

    cleaned = mac_or_bssid.strip().upper().replace("-", ":")
    match = re.match(r"^([0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2})", cleaned)
    if not match:
        return "Unknown"

    prefix = match.group(1)

    if prefix in _external_table:
        return _external_table[prefix]
    if prefix in _BUILTIN_OUI:
        return _BUILTIN_OUI[prefix]

    # Locally administered addresses (2nd hex digit of first octet is
    # 2, 6, A, or E) indicate a randomized/private MAC — very common
    # on modern iOS/Android for privacy. No vendor can be determined.
    first_octet = int(prefix[0:2], 16)
    if first_octet & 0x02:
        return "Private/Randomized Address"

    return "Unknown"


if __name__ == "__main__":
    tests = ["AC:87:A3:11:22:33", "1C:5A:3E:AA:BB:CC", "02:11:22:33:44:55", ""]
    for t in tests:
        print(f"{t or '(empty)':<25} -> {lookup_vendor(t)}")
