# 📡 R.A.D.A.R.
### Real-Time Device Activity Radar

**Discover. Visualize. Understand Your Wireless Environment.**

R.A.D.A.R. is an open-source Python desktop application that discovers nearby **Bluetooth Low Energy (BLE) devices and Wi-Fi networks** and displays their activity on a real-time, animated radar interface.

Using Received Signal Strength Indicator (RSSI), R.A.D.A.R. provides an approximate visualization of wireless proximity, device activity, and signal history.

Designed for developers, students, networking enthusiasts, and cybersecurity learners.

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-informational)](https://github.com/kabilansri2008-gif/NearbyRadar)
[![GitHub](https://img.shields.io/badge/GitHub-NearbyRadar-black?logo=github)](https://github.com/kabilansri2008-gif/NearbyRadar)
[![Open Source](https://img.shields.io/badge/Open%20Source-Contributions%20Welcome-brightgreen)](https://github.com/kabilansri2008-gif/NearbyRadar)

---

## 🌟 Project Overview

Wireless signals surround us every day, but their activity is usually invisible.

**R.A.D.A.R. makes nearby wireless activity easier to explore and understand.**

The application scans for discoverable BLE devices and Wi-Fi networks, estimates relative proximity from signal strength, and visualizes the results through an interactive radar display.

It also maintains a local history of detected devices, helping users observe changes in their wireless environment.

### 🎯 Project Objectives

- Visualize nearby wireless activity in real time.
- Discover BLE devices and Wi-Fi access points.
- Estimate relative proximity using RSSI.
- Classify devices using available broadcast information.
- Maintain a local database of device sightings.
- Provide interactive signal visualizations and alerts.
- Support wireless networking and cybersecurity education.

---

## 🚀 Key Features

| Feature | Description |
|---|---|
| 📡 Real-Time Radar | Animated visualization of detected wireless devices |
| 🔵 Bluetooth Scanning | Discover nearby BLE devices |
| 📶 Wi-Fi Discovery | Detect nearby Wi-Fi networks |
| 📏 Signal Analysis | Estimate relative proximity using RSSI |
| 🏭 Vendor Identification | Offline manufacturer lookup using MAC prefixes |
| 📱 Device Classification | Best-effort identification of device categories |
| 🌀 Motion Trails | Visualize recent changes in signal strength |
| 🗺️ Activity Heatmap | Display accumulated wireless activity |
| 🔊 Sonar Feedback | Audio feedback based on signal strength |
| 🗃️ Device History | Store previous sightings using SQLite |
| 🔔 Smart Notifications | Alert when selected devices enter or leave range |
| 📤 Data Export | Export results to CSV or JSON |
| 🧪 Demonstration Mode | Explore the interface using simulated device data |

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application development |
| Bleak | Bluetooth Low Energy scanning |
| Windows netsh | Wi-Fi network discovery on Windows |
| Linux nmcli | Wi-Fi network discovery on Linux |
| SQLite | Local device history storage |
| Plyer | Desktop notifications |
| CSV / JSON | Data export |

The project uses a modular Python architecture to separate scanning, visualization, history, and notification functionality.

---

## ⚙️ Installation and Setup

### Prerequisites

Before running the application, ensure your system has:

- Python 3.9 or newer
- Bluetooth adapter
- Wi-Fi adapter
- Git
- Supported operating system: Windows, Linux, or macOS

### Step 1 — Clone the repository

```bash
git clone https://github.com/kabilansri2008-gif/NearbyRadar.git
cd NearbyRadar
```

### Step 2 — Create a virtual environment

```bash
python -m venv venv
```

Activate the environment.

**Windows:**

```powershell
venv\Scripts\activate
```

**Linux / macOS:**

```bash
source venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Launch R.A.D.A.R.

```bash
python main.py
```

The application will launch its radar interface and begin scanning using available wireless adapters.

If supported scanners are unavailable, demonstration data may be used.

---

## 🖥️ How to Use

**1. Launch the application**

Start R.A.D.A.R. using `python main.py`.

**2. Scan nearby wireless activity**

Use **Rescan Now** to refresh detected devices and networks.

**3. Explore the radar**

Detected devices appear as points on the radar. Their relative distance from the center represents estimated proximity based on RSSI.

**4. View device details**

Select a radar point to inspect available device information, such as name, vendor, RSSI, and signal history.

**5. Enable advanced visualization**

Use Heatmap, Motion Trails, and Sonar Mode to explore wireless activity.

**6. Monitor selected devices**

Use Watch Mode to receive notifications when a selected device appears or disappears from detection range.

**7. Export results**

Save scan data as CSV or JSON for further analysis.

---

## 🧩 Project Architecture

```text
NearbyRadar/
│
├── main.py
│   └── Application entry point
│
├── radar_ui.py
│   └── Interactive radar visualization
│
├── ble_scanner.py
│   └── Bluetooth Low Energy discovery
│
├── wifi_scanner.py
│   └── Wi-Fi network scanning
│
├── oui_lookup.py
│   └── Manufacturer identification
│
├── device_type.py
│   └── Device classification
│
├── device_db.py
│   └── SQLite device history
│
├── notifier.py
│   └── Desktop alerts
│
├── exporter.py
│   └── CSV and JSON exports
│
├── sonar.py
│   └── Audio proximity feedback
│
└── requirements.txt
    └── Python dependencies
```

### 🔄 Application Workflow

```text
           Application Launch
                    |
                    v
            Initialize Scanners
                    |
          +---------+---------+
          |                   |
          v                   v
    BLE Discovery       Wi-Fi Discovery
          |                   |
          +---------+---------+
                    |
                    v
             Collect RSSI
                    |
                    v
          Classify Devices
                    |
                    v
         Update SQLite History
                    |
                    v
        Real-Time Radar Display
                    |
          +---------+---------+
          |         |         |
          v         v         v
       Heatmap   Alerts     Export
```

---

## 🖥️ Platform Compatibility

| Operating System | Wi-Fi Scanning | BLE Scanning |
|---|---|---|
| Windows | netsh | Bleak |
| Linux | nmcli | Bleak / BlueZ |
| macOS | System networking tools | Bleak |

**Platform notes:**

- Enable Bluetooth and Wi-Fi before scanning.
- Some platforms require Bluetooth or Location permissions.
- Device discovery depends on adapter capabilities and operating-system restrictions.
- Certain Wi-Fi scanning features may vary between operating systems.

---

## 📊 Understanding Signal Strength

R.A.D.A.R. uses **RSSI (Received Signal Strength Indicator)** to approximate relative device proximity.

| RSSI (dBm) | Typical Interpretation |
|---|---|
| -30 to -50 | Very strong signal |
| -51 to -65 | Strong signal |
| -66 to -75 | Moderate signal |
| -76 to -90 | Weak signal |
| Below -90 | Very weak signal |

These values are illustrative and can vary significantly between devices and environments.

**Important:** RSSI does not provide precise physical distance or direction. Radar positions are visual estimates, not actual device coordinates.

---

## 🔐 Privacy and Responsible Use

R.A.D.A.R. is intended for educational, diagnostic, and authorized wireless-environment analysis.

The application:

- Uses information broadcast by nearby devices and access points.
- Does not identify the people who own detected devices.
- Does not access private messages, phone numbers, or device files.
- Does not bypass operating-system security restrictions.
- Stores scan history locally in SQLite.
- Does not require cloud storage for device history.

**Privacy reminder:** Broadcast identifiers may still be sensitive. Use the application only in environments where you are authorized to scan, and do not use it to monitor or track people without consent.

Modern devices may randomize Bluetooth addresses, making historical matching and manufacturer identification unreliable.

---

## 🗃️ Local Data Storage

R.A.D.A.R. maintains a SQLite database named:

```text
radar_history.db
```

The database can store:

- Broadcast device identifiers
- Available device names
- Manufacturer information
- RSSI measurements
- First and last detection times
- Device sighting history

To clear the stored history, close the application and delete `radar_history.db`.

Exported CSV and JSON files should be handled carefully because they may contain wireless identifiers.

---

## 🧰 Troubleshooting

### Bluetooth devices are not appearing

- Verify that Bluetooth is enabled.
- Check system permissions.
- Confirm that your adapter supports BLE.
- Restart the application.
- Reinstall dependencies if necessary.

### Wi-Fi networks are not detected

- Ensure Wi-Fi is enabled.
- Verify that `netsh` or `nmcli` is available on the relevant platform.
- Check operating-system permissions and adapter support.

### Notifications are not displayed

- Enable desktop notifications.
- Check system notification permissions.
- Inspect terminal output for fallback alerts.

### Radar shows simulated devices

The application may be using demonstration mode because a scanner is unavailable.

Demonstration data does not represent actual nearby devices.

---

## 🤝 Contributing

Contributions are welcome!

You can help improve:

- Bluetooth and Wi-Fi scanning reliability
- Cross-platform compatibility
- Radar visualization and animations
- Documentation and tutorials
- Performance and usability
- Testing and bug fixes

### Contribution Steps

1. Fork the repository.
2. Create a feature branch.
3. Make your changes.
4. Test the application.
5. Commit your changes.
6. Push your branch.
7. Open a pull request describing your improvements.

```bash
git checkout -b feature/my-improvement
git add .
git commit -m "Improve radar functionality"
git push origin feature/my-improvement
```

Please keep contributions focused, documented, and consistent with the project's privacy principles.

---

## 🛣️ Future Enhancements

Potential improvements include:

- Advanced signal filtering and smoothing
- Improved device classification
- Configurable radar themes
- Additional data visualization
- Improved cross-platform support
- Performance optimizations
- Enhanced scan-history analytics

---

## 👨‍💻 Project Maintainer

**M. Kabilan**

B.Tech — Information Technology

St. Joseph's Institute of Technology

Interested in Python Development, Full-Stack Development, Cybersecurity, and Open-Source Software.

**GitHub:** [@kabilansri2008-gif](https://github.com/kabilansri2008-gif)

**Repository:** [NearbyRadar](https://github.com/kabilansri2008-gif/NearbyRadar)

---

## 📄 License

Refer to the repository's [LICENSE](https://github.com/kabilansri2008-gif/NearbyRadar/blob/main/LICENSE) file for the applicable license terms.

---

### ⭐ Support the Project

If you find R.A.D.A.R. useful, consider starring the repository, reporting issues, or contributing improvements.

**R.A.D.A.R. — Making Invisible Wireless Activity Visible.** 📡
