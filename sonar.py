"""
sonar.py

Turns the strongest nearby signal into an audible proximity cue —
like a parking sensor or Geiger counter. As a device's RSSI improves
(gets closer), the beep interval shortens and pitch rises. As it
weakens (moves away), beeps slow down and drop in pitch.

No external sound files: tones are synthesized on the fly as raw PCM
sine waves and handed directly to pygame.mixer.Sound. Tones are
cached per (frequency, duration) pair so we're not resynthesizing
audio every frame.
"""

import math
import struct
import time

import pygame

SAMPLE_RATE = 44100
_tone_cache = {}


def _make_tone(frequency: float, duration: float, volume: float = 0.4) -> pygame.mixer.Sound:
    """Synthesize a short sine-wave beep as a pygame Sound."""
    key = (round(frequency), round(duration, 3))
    if key in _tone_cache:
        return _tone_cache[key]

    n_samples = int(SAMPLE_RATE * duration)
    amplitude = int(32767 * volume)
    samples = bytearray()

    # simple attack/decay envelope so beeps don't click
    fade_samples = max(1, int(n_samples * 0.1))

    for i in range(n_samples):
        t = i / SAMPLE_RATE
        raw = math.sin(2 * math.pi * frequency * t)

        if i < fade_samples:
            envelope = i / fade_samples
        elif i > n_samples - fade_samples:
            envelope = (n_samples - i) / fade_samples
        else:
            envelope = 1.0

        value = int(raw * amplitude * envelope)
        # stereo, 16-bit signed little-endian
        packed = struct.pack("<hh", value, value)
        samples += packed

    sound = pygame.mixer.Sound(buffer=bytes(samples))
    _tone_cache[key] = sound
    return sound


class SonarEngine:
    """
    Call `update(closest_strength)` every frame with a 0..1 value
    (1.0 = strongest/closest signal seen, 0.0 = weakest/farthest or
    no devices). It handles timing and pitch/interval scaling and
    plays a beep exactly when one is due.
    """

    def __init__(self):
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2)
        self.enabled = False
        self._last_beep_time = 0.0

    def toggle(self):
        self.enabled = not self.enabled

    def update(self, closest_strength: float):
        """
        closest_strength: 0.0 (nothing nearby / very far) to 1.0
        (very close / strong signal).
        """
        if not self.enabled or closest_strength <= 0.02:
            return

        # interval: 1.4s when far (strength ~0) down to ~0.12s when very close
        interval = 1.4 - (1.28 * closest_strength)
        interval = max(0.12, interval)

        now = time.time()
        if now - self._last_beep_time >= interval:
            self._last_beep_time = now
            # pitch: 300Hz far -> 1000Hz close
            freq = 300 + (700 * closest_strength)
            duration = 0.07
            tone = _make_tone(freq, duration)
            tone.play()
