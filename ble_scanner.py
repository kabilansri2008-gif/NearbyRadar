"""
ble_scanner.py

Scans for nearby Bluetooth Low Energy (BLE) devices using the `bleak`
library and returns whatever information the devices are already
broadcasting publicly (device name if set, MAC/UUID address, and
signal strength / RSSI).

IMPORTANT:
This only reads information devices choose to broadcast openly over
BLE advertisement packets. It cannot determine a real person's
identity, phone number, or any private information. Many devices
broadcast no name at all, or a generic manufacturer name.
"""

import asyncio
from dataclasses import dataclass
from typing import List

try:
    from bleak import BleakScanner
except ImportError:
    BleakScanner = None


@dataclass
class DetectedDevice:
    address: str          # MAC address / UUID (identifier, not identity)
    name: str              # Broadcast name, or "Unknown Device"
    rssi: int              # Signal strength in dBm (negative number)
    source: str = "BLE"    # BLE or WiFi

    def estimated_distance_m(self) -> float:
        """
        Rough distance estimate from RSSI using the log-distance path
        loss model. This is approximate — real-world accuracy varies
        a lot depending on obstacles, phone orientation, etc.
        """
        tx_power = -59  # calibrated RSSI at 1 meter (typical BLE beacon default)
        if self.rssi == 0:
            return -1.0
        ratio = (tx_power - self.rssi) / (10 * 2.0)  # path-loss exponent n=2
        return round(10 ** ratio, 2)


async def scan_ble(duration: float = 5.0) -> List[DetectedDevice]:
    """
    Scan for nearby BLE devices for `duration` seconds.
    Returns a list of DetectedDevice.
    """
    if BleakScanner is None:
        raise RuntimeError(
            "bleak is not installed. Run: pip install bleak"
        )

    devices = await BleakScanner.discover(timeout=duration, return_adv=True)

    results = []
    for address, (device, adv) in devices.items():
        name = device.name or adv.local_name or "Unknown Device"
        rssi = adv.rssi if adv.rssi is not None else -100
        results.append(DetectedDevice(address=address, name=name, rssi=rssi))

    # Strongest signal (closest) first
    results.sort(key=lambda d: d.rssi, reverse=True)
    return results


if __name__ == "__main__":
    found = asyncio.run(scan_ble(5.0))
    print(f"Found {len(found)} BLE device(s):\n")
    for d in found:
        print(f"  {d.name:<30} {d.address:<20} RSSI: {d.rssi} dBm  "
              f"(~{d.estimated_distance_m()} m)")
