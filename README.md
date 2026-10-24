# 📡 R.A.D.A.R. — Real-Time Device Activity Radar

A desktop app that turns nearby Bluetooth Low Energy (BLE) and Wi-Fi activity into an interactive, animated radar. It reads only what devices and access points **publicly broadcast**, estimates relative proximity from signal strength (RSSI), and keeps a local history so you can see what's new and what's changed.

> **Responsible use:** R.A.D.A.R. is for understanding your own radio environment (home, lab, office, learning). Do not use it to monitor or track people without their knowledge and consent.

---

## Contents

- [Features](#features)
- [What it can and cannot do](#what-it-can-and-cannot-do)
- [Quick start](#quick-start)
- [Using the app](#using-the-app)
- [Platform notes](#platform-notes)
- [Data and privacy](#data-and-privacy)
- [Accuracy](#accuracy)
- [Troubleshooting](#troubleshooting)
- [Project structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

---

## Features

| Feature | Description |
| --- | --- |
| 🛰️ Live radar | Detected devices appear as moving points; distance from center reflects signal strength |
| 🔵 BLE + 📶 Wi-Fi scanning | Discovers nearby BLE devices and Wi-Fi networks |
| 🏭 Vendor lookup | Offline MAC-prefix (OUI) database, no internet needed |
| 📱 Device classification | Best-effort labels: phone, laptop, watch, speaker, other |
| 🌀 Motion trails & 💡 signal pulse | Recent movement and animation tied to signal strength |
| 🗺️ Activity heatmap | Shows where activity has accumulated over time |
| 🔊 Sonar mode | Audio feedback that rises with signal strength |
| 🆕 Local history | SQLite log of past sightings: NEW badges, seen-count, RSSI graphs |
| 🔔 Watch mode | Desktop notification when a selected device enters or leaves range |
| 📤 Export | Save scan results as CSV or JSON |

## What it can and cannot do

R.A.D.A.R. works only with broadcast data. It **cannot**:

- identify the person who owns a device, or infer identity from a device name
- obtain phone numbers or any private or contact information
- read data from other devices or bypass OS privacy protections

Many modern devices use **randomized Bluetooth addresses**, so vendor and history matching may be incomplete or inconsistent.

---

## Quick start

**Requirements:** Python 3.9+, a Bluetooth adapter, a Wi-Fi adapter.

```bash
cd NearbyRadar

# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python main.py
```

---

## Using the app

| Control | What it does |
| --- | --- |
| **Rescan Now** | Starts a new scan immediately |
| **Heatmap** | Toggles accumulated-activity overlay |
| **Sonar** | Audio proximity feedback. Follows the selected device, otherwise the strongest signal |
| **Click a point** | Opens the details panel: name, vendor, RSSI, signal history |
| **Watch** | Notifies you when the selected device enters or leaves range |
| **Export** | Saves current results as `CSV` or `JSON` |
| **ESC** | Exit |

---

## Platform notes

| OS | Wi-Fi scanning | Bluetooth | Notes |
| --- | --- | --- | --- |
| 🪟 Windows | `netsh wlan show networks` | `bleak` | Wi-Fi and Bluetooth must be on |
| 🐧 Linux | `nmcli` (`sudo apt install network-manager` if missing) | `bleak` + BlueZ | May need your user in the `bluetooth` group or elevated permissions |
| 🍎 macOS | System networking tools | `bleak` | Grant Bluetooth (and, if prompted, Location) permission to your terminal or editor |

If a scanner is unavailable, the app can fall back to **demonstration data**. Demo data is simulated and does not represent real nearby devices.

**Notifications** use `plyer`. If your OS blocks them, alerts are printed to the terminal instead.

---

## Data and privacy

- All history is stored **locally** in `radar_history.db` (SQLite). Nothing is uploaded.
- Stored: device identifier as broadcast, broadcast name, vendor, RSSI samples, first/last seen times.
- To reset history, close the app and delete `radar_history.db`.
- Exports (CSV/JSON) contain the same scan data. Treat them as sensitive if they include devices that aren't yours.

---

## Accuracy

Distance is an **estimate**, not a measurement. RSSI is affected by:

- 🧱 walls and obstacles
- 📡 interference from other radios
- 📱 device orientation and body position
- 📶 antenna and chipset differences

Use position on the radar as "closer / farther", not as meters.

---

## Troubleshooting

**No Bluetooth devices appear**
1. Confirm Bluetooth is on.
2. Confirm your OS has granted Bluetooth permission to your terminal / Python.
3. Reinstall dependencies: `pip install -r requirements.txt`, then restart `python main.py`.

**Wi-Fi scan doesn't work**
Confirm `netsh` (Windows) or `nmcli` (Linux) is available and Wi-Fi is enabled. Otherwise the app falls back to demo data.

**No notifications**
Enable desktop notifications for your Python environment. Otherwise alerts appear in the terminal.

---

## Project structure

```text
NearbyRadar/
├── main.py            # Entry point
├── radar_ui.py        # Radar interface and visualization
├── ble_scanner.py     # BLE scanning
├── wifi_scanner.py    # Wi-Fi discovery
├── oui_lookup.py      # Offline manufacturer lookup
├── device_type.py     # Device-type classification
├── device_db.py       # SQLite device history
├── notifier.py        # Desktop notifications
├── exporter.py        # CSV / JSON export
├── sonar.py           # Audio proximity feedback
└── requirements.txt   # Python dependencies
```

---

## Contributing

Improvements to docs, usability, reliability, platform compatibility, and visualization are welcome.

1. Create a branch
2. Make and test your changes
3. Commit with a clear message
4. Open a pull request explaining what changed and why

## License

See the repository's `LICENSE` file.
