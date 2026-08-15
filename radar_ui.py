"""
radar_ui.py

Graphical "radar" display built with pygame. Draws a sweeping radar
line and plots blips for every detected Bluetooth / Wi-Fi device,
plus a set of "innovation" features layered on top of the basic scan:

  - Fading motion trails per device (last few positions)
  - Pulse animation scaled by signal strength
  - Simple device-type icons (phone/headphones/watch/laptop/speaker/tv)
  - Heatmap mode: accumulates activity over time across the room
  - NEW vs returning device tagging (via local SQLite history)
  - Click a blip to pin it and see a live RSSI-over-time mini graph
  - Watch/alert a pinned device: desktop notification on enter/leave
  - Export current scan to CSV or JSON

Run:
    python main.py
"""

import math
import sys
import time
import hashlib
import threading
import asyncio
from collections import deque

import pygame

from ble_scanner import scan_ble
from wifi_scanner import scan_wifi
from oui_lookup import lookup_vendor
from device_type import classify as classify_device_type
import device_db
import notifier
import exporter
from sonar import SonarEngine

WIDTH, HEIGHT = 900, 800
CENTER = (450, 400)
MAX_RADIUS = 340
BG_COLOR = (5, 15, 5)
SWEEP_COLOR = (0, 255, 70)
GRID_COLOR = (0, 90, 30)
TEXT_COLOR = (170, 255, 170)
BLIP_COLOR_BLE = (0, 255, 120)
BLIP_COLOR_WIFI = (255, 200, 0)
NEW_TAG_COLOR = (255, 90, 90)
PANEL_BG = (10, 25, 12)

RESCAN_INTERVAL = 8.0
TRAIL_LENGTH = 6            # how many past positions to remember per device
DEVICE_TIMEOUT = 25.0        # seconds of absence before a "leave" alert fires
HEATMAP_GRID = 48            # heatmap resolution (cells across the diameter)


class TrackedDevice:
    """Holds live + historical state for one device across scans."""

    def __init__(self, address, name, kind, angle, distance_ratio, rssi, vendor, dtype):
        self.address = address
        self.name = name
        self.kind = kind
        self.angle = angle
        self.distance_ratio = distance_ratio
        self.rssi = rssi
        self.vendor = vendor
        self.dtype = dtype

        self.trail = deque(maxlen=TRAIL_LENGTH)
        self.rssi_history = deque(maxlen=60)
        self.last_seen = time.time()
        self.first_seen_session = time.time()
        self.is_new_today = False
        self.times_seen_total = 1
        self.watched = False
        self.present = True

    def update(self, angle, distance_ratio, rssi):
        self.trail.append((self.angle, self.distance_ratio))
        self.angle = angle
        self.distance_ratio = distance_ratio
        self.rssi = rssi
        self.rssi_history.append(rssi)
        self.last_seen = time.time()
        self.present = True


class RadarApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("R.A.D.A.R - Device Presence Radar")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 13)
        self.small_font = pygame.font.SysFont("consolas", 11)
        self.title_font = pygame.font.SysFont("consolas", 20, bold=True)

        self.sweep_angle = 0.0
        self.tracked = {}   # address -> TrackedDevice
        self.lock = threading.Lock()
        self.status = "Starting first scan..."
        self.is_scanning = False

        self.heatmap = [[0.0] * HEATMAP_GRID for _ in range(HEATMAP_GRID)]
        self.heatmap_mode = False

        self.selected_address = None  # pinned device for the side panel
        self.sonar = SonarEngine()

        # Buttons
        self.rescan_button_rect = pygame.Rect(WIDTH - 180, 70, 160, 32)
        self.heatmap_button_rect = pygame.Rect(WIDTH - 180, 110, 160, 32)
        self.sonar_button_rect = pygame.Rect(WIDTH - 180, 150, 160, 32)
        self.export_csv_rect = pygame.Rect(WIDTH - 180, 190, 76, 32)
        self.export_json_rect = pygame.Rect(WIDTH - 96, 190, 76, 32)
        self.watch_button_rect = pygame.Rect(WIDTH - 180, 540, 160, 32)

        self._rescan_event = threading.Event()
        self._rescan_event.set()

        self._start_background_scanning()
        self._start_alert_watcher()

    # ---------- scanning ----------

    def _start_background_scanning(self):
        threading.Thread(target=self._scan_loop, daemon=True).start()

    def request_rescan(self):
        if not self.is_scanning:
            self._rescan_event.set()

    def _scan_loop(self):
        while True:
            self._rescan_event.wait(timeout=RESCAN_INTERVAL)
            self._rescan_event.clear()

            self.is_scanning = True
            self.status = "Scanning..."
            try:
                ble_results = asyncio.run(scan_ble(duration=4.0))
            except Exception as e:
                ble_results = []
                print(f"[radar_ui] BLE scan error: {e}")

            try:
                wifi_results = scan_wifi()
            except Exception as e:
                wifi_results = []
                print(f"[radar_ui] WiFi scan error: {e}")

            seen_this_scan = set()

            with self.lock:
                for d in ble_results:
                    self._ingest(d.address, d.name, "BLE", d.rssi)
                    seen_this_scan.add(d.address)

                for w in wifi_results:
                    addr = w.bssid or f"ssid:{w.ssid}"
                    self._ingest(addr, w.ssid, "WiFi", w.rssi_estimate())
                    seen_this_scan.add(addr)

                # mark absent devices as not-present (for leave alerts)
                for addr, dev in self.tracked.items():
                    if addr not in seen_this_scan:
                        dev.present = False

                self.status = (f"Last scan: {time.strftime('%H:%M:%S')}  "
                                f"({len(seen_this_scan)} device(s) found)")

            self.is_scanning = False

    def _ingest(self, address, name, kind, rssi):
        vendor = lookup_vendor(address if kind == "BLE" else address)
        dtype = classify_device_type(name)
        angle, distance_ratio = self._to_polar(address, kind, rssi)

        device_db.record_sighting(address, name, kind, rssi, vendor)
        stats = device_db.get_device_stats(address)

        if address in self.tracked:
            dev = self.tracked[address]
            dev.update(angle, distance_ratio, rssi)
            dev.name = name
            dev.vendor = vendor
        else:
            dev = TrackedDevice(address, name, kind, angle, distance_ratio,
                                 rssi, vendor, dtype)
            self.tracked[address] = dev

        if stats:
            dev.is_new_today = stats.is_new_today and stats.total_sightings <= 3
            dev.times_seen_total = stats.total_sightings

        self._paint_heatmap(angle, distance_ratio)

    def _to_polar(self, address, kind, rssi):
        h = hashlib.md5(f"{kind}:{address}".encode()).hexdigest()
        angle = int(h[:8], 16) % 360

        rssi_clamped = max(-100, min(-30, rssi))
        distance_ratio = 1 - ((rssi_clamped + 100) / 70)
        distance_ratio = max(0.08, min(1.0, distance_ratio))
        return angle, distance_ratio

    def _paint_heatmap(self, angle, distance_ratio):
        rad = math.radians(angle)
        r = distance_ratio * MAX_RADIUS
        x = CENTER[0] + r * math.cos(rad)
        y = CENTER[1] + r * math.sin(rad)

        gx = int((x - (CENTER[0] - MAX_RADIUS)) / (2 * MAX_RADIUS) * HEATMAP_GRID)
        gy = int((y - (CENTER[1] - MAX_RADIUS)) / (2 * MAX_RADIUS) * HEATMAP_GRID)
        if 0 <= gx < HEATMAP_GRID and 0 <= gy < HEATMAP_GRID:
            self.heatmap[gy][gx] = min(1.0, self.heatmap[gy][gx] + 0.15)

    # ---------- alerts ----------

    def _start_alert_watcher(self):
        threading.Thread(target=self._alert_loop, daemon=True).start()

    def _alert_loop(self):
        known_presence = {}
        while True:
            time.sleep(2.0)
            with self.lock:
                for addr, dev in list(self.tracked.items()):
                    if not dev.watched:
                        continue
                    now = time.time()
                    currently_present = dev.present and (now - dev.last_seen) < DEVICE_TIMEOUT
                    was_present = known_presence.get(addr, False)

                    if currently_present and not was_present:
                        notifier.notify("R.A.D.A.R Alert",
                                         f"{dev.name} entered range.")
                    elif not currently_present and was_present:
                        notifier.notify("R.A.D.A.R Alert",
                                         f"{dev.name} left range.")

                    known_presence[addr] = currently_present

    # ---------- drawing ----------

    def draw_grid(self):
        for r in (0.25, 0.5, 0.75, 1.0):
            pygame.draw.circle(self.screen, GRID_COLOR, CENTER,
                                int(MAX_RADIUS * r), 1)
        pygame.draw.line(self.screen, GRID_COLOR,
                          (CENTER[0] - MAX_RADIUS, CENTER[1]),
                          (CENTER[0] + MAX_RADIUS, CENTER[1]), 1)
        pygame.draw.line(self.screen, GRID_COLOR,
                          (CENTER[0], CENTER[1] - MAX_RADIUS),
                          (CENTER[0], CENTER[1] + MAX_RADIUS), 1)

    def draw_heatmap(self):
        cell_size = (2 * MAX_RADIUS) / HEATMAP_GRID
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for gy in range(HEATMAP_GRID):
            for gx in range(HEATMAP_GRID):
                val = self.heatmap[gy][gx]
                if val <= 0.01:
                    continue
                x = (CENTER[0] - MAX_RADIUS) + gx * cell_size
                y = (CENTER[1] - MAX_RADIUS) + gy * cell_size
                intensity = min(1.0, val)
                color = (int(255 * intensity), int(80 * (1 - intensity)), 0,
                         int(120 * intensity))
                pygame.draw.rect(overlay, color, (x, y, cell_size, cell_size))
        self.screen.blit(overlay, (0, 0))
        for row in self.heatmap:
            for i in range(len(row)):
                row[i] *= 0.997

    def draw_sweep(self):
        rad = math.radians(self.sweep_angle)
        end = (CENTER[0] + MAX_RADIUS * math.cos(rad),
               CENTER[1] + MAX_RADIUS * math.sin(rad))
        pygame.draw.line(self.screen, SWEEP_COLOR, CENTER, end, 2)
        for i in range(1, 40, 4):
            trail_angle = math.radians(self.sweep_angle - i)
            alpha_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            trail_end = (CENTER[0] + MAX_RADIUS * math.cos(trail_angle),
                         CENTER[1] + MAX_RADIUS * math.sin(trail_angle))
            pygame.draw.line(alpha_surf, (0, 255, 70, max(0, 60 - i)),
                              CENTER, trail_end, 2)
            self.screen.blit(alpha_surf, (0, 0))

    def _polar_to_xy(self, angle, distance_ratio):
        rad = math.radians(angle)
        r = distance_ratio * MAX_RADIUS
        return CENTER[0] + r * math.cos(rad), CENTER[1] + r * math.sin(rad)

    def draw_trail(self, dev):
        points = list(dev.trail) + [(dev.angle, dev.distance_ratio)]
        n = len(points)
        for i in range(n - 1):
            a1, d1 = points[i]
            a2, d2 = points[i + 1]
            x1, y1 = self._polar_to_xy(a1, d1)
            x2, y2 = self._polar_to_xy(a2, d2)
            alpha = int(200 * (i + 1) / n)
            color = BLIP_COLOR_BLE if dev.kind == "BLE" else BLIP_COLOR_WIFI
            surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.line(surf, (*color, alpha), (x1, y1), (x2, y2), 2)
            self.screen.blit(surf, (0, 0))

    def draw_icon(self, x, y, dtype, color):
        s = 6
        if dtype == "phone":
            pygame.draw.rect(self.screen, color, (x - 4, y - 7, 8, 14), 1, border_radius=2)
        elif dtype == "headphone":
            pygame.draw.arc(self.screen, color, (x - 7, y - 7, 14, 14), 0.3, 2.8, 2)
        elif dtype == "watch":
            pygame.draw.rect(self.screen, color, (x - 5, y - 5, 10, 10), 1, border_radius=3)
        elif dtype == "laptop":
            pygame.draw.rect(self.screen, color, (x - 7, y - 4, 14, 8), 1)
        elif dtype == "speaker":
            pygame.draw.circle(self.screen, color, (x, y), 6, 1)
            pygame.draw.circle(self.screen, color, (x, y), 2, 1)
        elif dtype == "tv":
            pygame.draw.rect(self.screen, color, (x - 8, y - 5, 16, 10), 1)
        else:
            pygame.draw.circle(self.screen, color, (x, y), s, 1)

    def draw_devices(self):
        with self.lock:
            devices = list(self.tracked.values())

        pulse = (math.sin(time.time() * 4) + 1) / 2  # 0..1

        for dev in devices:
            if self.heatmap_mode:
                continue  # keep heatmap view uncluttered

            self.draw_trail(dev)
            x, y = self._polar_to_xy(dev.angle, dev.distance_ratio)
            color = BLIP_COLOR_BLE if dev.kind == "BLE" else BLIP_COLOR_WIFI

            strength = 1 - dev.distance_ratio  # 0..1, closer = stronger
            radius = 5 + int(4 * strength * pulse)

            is_selected = dev.address == self.selected_address
            if is_selected:
                pygame.draw.circle(self.screen, (255, 255, 255), (int(x), int(y)), radius + 6, 1)

            pygame.draw.circle(self.screen, color, (int(x), int(y)), radius)
            pygame.draw.circle(self.screen, color, (int(x), int(y)), radius + 4, 1)
            self.draw_icon(int(x), int(y), dev.dtype, (10, 10, 10))

            label_text = f"{dev.name} ({dev.rssi}dBm)"
            label = self.small_font.render(label_text, True, TEXT_COLOR)
            self.screen.blit(label, (x + 10, y - 14))

            if dev.is_new_today:
                tag = self.small_font.render("NEW", True, NEW_TAG_COLOR)
                self.screen.blit(tag, (x + 10, y))
            elif dev.times_seen_total > 1:
                tag = self.small_font.render(f"seen {dev.times_seen_total}x", True, TEXT_COLOR)
                self.screen.blit(tag, (x + 10, y))

            if dev.watched:
                w = self.small_font.render("* watched", True, (255, 210, 80))
                self.screen.blit(w, (x + 10, y + 12))

    # ---------- side panel ----------

    def draw_side_panel(self):
        panel_rect = pygame.Rect(WIDTH - 180, 230, 172, 300)
        pygame.draw.rect(self.screen, PANEL_BG, panel_rect, border_radius=6)
        pygame.draw.rect(self.screen, GRID_COLOR, panel_rect, 1, border_radius=6)

        if not self.selected_address:
            hint = self.small_font.render("Click a blip to", True, TEXT_COLOR)
            hint2 = self.small_font.render("pin device details", True, TEXT_COLOR)
            self.screen.blit(hint, (panel_rect.x + 10, panel_rect.y + 12))
            self.screen.blit(hint2, (panel_rect.x + 10, panel_rect.y + 30))
            return

        with self.lock:
            dev = self.tracked.get(self.selected_address)
        if not dev:
            self.selected_address = None
            return

        y = panel_rect.y + 10
        lines = [
            (dev.name, TEXT_COLOR, self.font),
            (f"Kind: {dev.kind}", TEXT_COLOR, self.small_font),
            (f"Vendor: {dev.vendor}", TEXT_COLOR, self.small_font),
            (f"RSSI: {dev.rssi} dBm", TEXT_COLOR, self.small_font),
            (f"Seen: {dev.times_seen_total}x total", TEXT_COLOR, self.small_font),
        ]
        for text, color, font in lines:
            surf = font.render(text[:26], True, color)
            self.screen.blit(surf, (panel_rect.x + 8, y))
            y += 18

        y += 6
        graph_rect = pygame.Rect(panel_rect.x + 8, y, panel_rect.width - 16, 90)
        pygame.draw.rect(self.screen, (0, 20, 5), graph_rect)
        pygame.draw.rect(self.screen, GRID_COLOR, graph_rect, 1)

        history = list(dev.rssi_history)
        if len(history) >= 2:
            lo, hi = min(history), max(history)
            span = max(1, hi - lo)
            points = []
            for i, val in enumerate(history):
                px = graph_rect.x + (i / (len(history) - 1)) * graph_rect.width
                py = graph_rect.bottom - ((val - lo) / span) * graph_rect.height
                points.append((px, py))
            pygame.draw.lines(self.screen, BLIP_COLOR_BLE, False, points, 2)

        y = graph_rect.bottom + 10
        watch_label = "Unwatch" if dev.watched else "Watch (alerts)"
        self.watch_button_rect.y = y
        pygame.draw.rect(self.screen, (0, 90, 30), self.watch_button_rect, border_radius=6)
        pygame.draw.rect(self.screen, SWEEP_COLOR, self.watch_button_rect, 1, border_radius=6)
        wl = self.small_font.render(watch_label, True, (230, 255, 230))
        self.screen.blit(wl, wl.get_rect(center=self.watch_button_rect.center))

    # ---------- HUD & buttons ----------

    def draw_button(self, rect, label, active=False):
        mouse_pos = pygame.mouse.get_pos()
        hovering = rect.collidepoint(mouse_pos)
        if active:
            fill = (0, 150, 60)
        elif hovering:
            fill = (0, 120, 45)
        else:
            fill = (0, 80, 28)
        pygame.draw.rect(self.screen, fill, rect, border_radius=6)
        pygame.draw.rect(self.screen, SWEEP_COLOR, rect, 1, border_radius=6)
        text = self.small_font.render(label, True, (230, 255, 230))
        self.screen.blit(text, text.get_rect(center=rect.center))

    def draw_hud(self):
        title = self.title_font.render("R.A.D.A.R", True, SWEEP_COLOR)
        self.screen.blit(title, (20, 15))
        subtitle = self.font.render("Device Presence Radar", True, TEXT_COLOR)
        self.screen.blit(subtitle, (20, 42))
        status = self.font.render(self.status, True, TEXT_COLOR)
        self.screen.blit(status, (20, HEIGHT - 30))

        legend_ble = self.small_font.render("- Bluetooth", True, BLIP_COLOR_BLE)
        legend_wifi = self.small_font.render("- WiFi", True, BLIP_COLOR_WIFI)
        self.screen.blit(legend_ble, (WIDTH - 180, 20))
        self.screen.blit(legend_wifi, (WIDTH - 180, 40))

        rescan_label = "Scanning..." if self.is_scanning else "Rescan Now"
        self.draw_button(self.rescan_button_rect, rescan_label)
        self.draw_button(self.heatmap_button_rect,
                          "Heatmap: ON" if self.heatmap_mode else "Heatmap: OFF",
                          active=self.heatmap_mode)
        self.draw_button(self.sonar_button_rect,
                          "Sonar: ON" if self.sonar.enabled else "Sonar: OFF",
                          active=self.sonar.enabled)
        self.draw_button(self.export_csv_rect, "CSV")
        self.draw_button(self.export_json_rect, "JSON")

        self.draw_side_panel()

    # ---------- export ----------

    def _snapshot_for_export(self):
        with self.lock:
            devices = list(self.tracked.values())
        return [{
            "name": d.name,
            "kind": d.kind,
            "address": d.address,
            "rssi": d.rssi,
            "vendor": d.vendor,
            "distance_m": round(10 ** ((-59 - d.rssi) / 20), 2),
            "times_seen": d.times_seen_total,
            "first_seen_today": d.is_new_today,
        } for d in devices]

    # ---------- event handling ----------

    def handle_click(self, pos):
        if self.rescan_button_rect.collidepoint(pos):
            self.request_rescan()
            return
        if self.heatmap_button_rect.collidepoint(pos):
            self.heatmap_mode = not self.heatmap_mode
            return
        if self.sonar_button_rect.collidepoint(pos):
            self.sonar.toggle()
            return
        if self.export_csv_rect.collidepoint(pos):
            path = exporter.export_csv(self._snapshot_for_export())
            self.status = f"Exported CSV -> {path.name}"
            return
        if self.export_json_rect.collidepoint(pos):
            path = exporter.export_json(self._snapshot_for_export())
            self.status = f"Exported JSON -> {path.name}"
            return
        if self.selected_address and self.watch_button_rect.collidepoint(pos):
            with self.lock:
                dev = self.tracked.get(self.selected_address)
                if dev:
                    dev.watched = not dev.watched
            return

        with self.lock:
            for dev in self.tracked.values():
                x, y = self._polar_to_xy(dev.angle, dev.distance_ratio)
                if math.hypot(pos[0] - x, pos[1] - y) <= 12:
                    self.selected_address = dev.address
                    return

    # ---------- sonar ----------

    def _update_sonar(self):
        if not self.sonar.enabled:
            return
        with self.lock:
            devices = list(self.tracked.values())

        if not devices:
            self.sonar.update(0.0)
            return

        # closest = highest (1 - distance_ratio); prefer a pinned/watched
        # device if one is selected, otherwise use whichever is nearest
        if self.selected_address and self.selected_address in self.tracked:
            dev = self.tracked[self.selected_address]
            strength = 1 - dev.distance_ratio
        else:
            strength = max(1 - d.distance_ratio for d in devices)

        self.sonar.update(strength)

    # ---------- main loop ----------

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_click(event.pos)

            self.screen.fill(BG_COLOR)
            self.draw_grid()
            if self.heatmap_mode:
                self.draw_heatmap()
            self.draw_sweep()
            self.draw_devices()
            self.draw_hud()
            self._update_sonar()

            self.sweep_angle = (self.sweep_angle + 1.2) % 360
            pygame.display.flip()
            self.clock.tick(60)


if __name__ == "__main__":
    RadarApp().run()
