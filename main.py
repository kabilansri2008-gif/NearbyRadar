"""
main.py

Entry point for the R.A.D.A.R (Remote Area Device Awareness Radar)
project. Launches the graphical radar window which continuously
scans for nearby Bluetooth and Wi-Fi devices in the background and
plots them as blips on a sweeping radar display.

Usage:
    python main.py

Requires:
    pip install -r requirements.txt

Notes:
    - Bluetooth scanning requires Bluetooth to be turned on.
    - On Linux, BLE scanning via bleak generally needs BlueZ and may
      require running with appropriate permissions.
    - Wi-Fi scanning uses OS-native tools (netsh / nmcli / airport).
      If none are available, it falls back to demo data so the UI
      still works.
"""

from radar_ui import RadarApp

if __name__ == "__main__":
    print("Launching R.A.D.A.R... (close the window or press ESC to quit)")
    RadarApp().run()
