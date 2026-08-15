"""
wifi_scanner.py

Scans for nearby Wi-Fi access points / hotspots. This shows network
SSIDs (network names) and signal strength — NOT owner identities.
Many phones broadcast a personal hotspot name like "John's iPhone",
which is why you might see a first name here — that's the owner's
own choice, not something we extracted.

Cross-platform support (best effort):
  - Windows: uses `netsh wlan show networks mode=Bssid`
  - Linux:   uses `nmcli -f SSID,SIGNAL,BSSID dev wifi`
  - macOS:   uses the `airport` utility

If none of these are available (e.g. this sandboxed environment),
falls back to demo/mock data so the radar UI still has something
to render.
"""

import platform
import re
import subprocess
from dataclasses import dataclass
from typing import List


@dataclass
class WifiNetwork:
    ssid: str
    signal_percent: int   # 0-100
    bssid: str = ""
    source: str = "WiFi"

    def rssi_estimate(self) -> int:
        """Rough conversion from signal percent to dBm-like RSSI."""
        return int((self.signal_percent / 2) - 100)


def _scan_windows() -> List[WifiNetwork]:
    out = subprocess.check_output(
        ["netsh", "wlan", "show", "networks", "mode=Bssid"],
        text=True, errors="ignore"
    )
    networks = []
    current_ssid = None
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("SSID"):
            current_ssid = line.split(":", 1)[1].strip()
        elif line.startswith("Signal") and current_ssid is not None:
            pct = int(re.sub(r"[^\d]", "", line.split(":")[1]))
            networks.append(WifiNetwork(ssid=current_ssid or "Hidden Network",
                                         signal_percent=pct))
    return networks


def _scan_linux() -> List[WifiNetwork]:
    out = subprocess.check_output(
        ["nmcli", "-t", "-f", "SSID,SIGNAL,BSSID", "dev", "wifi"],
        text=True, errors="ignore"
    )
    networks = []
    for line in out.splitlines():
        parts = line.split(":")
        if len(parts) >= 2:
            ssid = parts[0] or "Hidden Network"
            try:
                signal = int(parts[1])
            except ValueError:
                signal = 0
            bssid = parts[2] if len(parts) > 2 else ""
            networks.append(WifiNetwork(ssid=ssid, signal_percent=signal, bssid=bssid))
    return networks


def _scan_macos() -> List[WifiNetwork]:
    airport = (
        "/System/Library/PrivateFrameworks/Apple80211.framework/"
        "Versions/Current/Resources/airport"
    )
    out = subprocess.check_output([airport, "-s"], text=True, errors="ignore")
    networks = []
    for line in out.splitlines()[1:]:
        cols = line.split()
        if len(cols) >= 3:
            ssid = cols[0]
            try:
                rssi = int(cols[2])
                pct = max(0, min(100, 2 * (rssi + 100)))
            except ValueError:
                pct = 0
            networks.append(WifiNetwork(ssid=ssid, signal_percent=pct))
    return networks


def _scan_demo() -> List[WifiNetwork]:
    """Fallback demo data when no OS Wi-Fi tool is available."""
    import random
    sample_names = [
        "Home Network", "Guest WiFi", "CoffeeShop_Free",
        "Alex's Hotspot", "NETGEAR-5G", "Office_WiFi"
    ]
    return [
        WifiNetwork(ssid=name, signal_percent=random.randint(20, 95))
        for name in sample_names
    ]


def scan_wifi() -> List[WifiNetwork]:
    system = platform.system()
    try:
        if system == "Windows":
            return _scan_windows()
        elif system == "Linux":
            return _scan_linux()
        elif system == "Darwin":
            return _scan_macos()
    except Exception as e:
        print(f"[wifi_scanner] Live scan failed ({e}), using demo data.")
    return _scan_demo()


if __name__ == "__main__":
    nets = scan_wifi()
    print(f"Found {len(nets)} WiFi network(s):\n")
    for n in sorted(nets, key=lambda x: x.signal_percent, reverse=True):
        print(f"  {n.ssid:<25} Signal: {n.signal_percent}%  "
              f"(~{n.rssi_estimate()} dBm)")
