"""
device_type.py

Guesses a general device category from its broadcast name, purely to
pick a nicer icon on the radar (phone / headphones / watch / laptop /
speaker / generic). This is a simple keyword heuristic — BLE doesn't
reliably expose a structured "device type" field across platforms, so
this is best-effort and just for visual flavor, not a real
fingerprinting technique.
"""

_KEYWORDS = {
    "phone":     ["iphone", "phone", "galaxy s", "galaxy note", "pixel", "redmi", "oneplus"],
    "headphone": ["airpods", "buds", "headphone", "earphone", "wf-", "beats"],
    "watch":     ["watch", "band", "fitbit", "garmin"],
    "laptop":    ["macbook", "laptop", "thinkpad", "notebook", "surface"],
    "speaker":   ["speaker", "soundbar", "jbl", "sonos", "echo", "boombox"],
    "tv":        ["tv", "roku", "chromecast", "firetv", "appletv"],
}


def classify(name: str) -> str:
    if not name:
        return "generic"
    lowered = name.lower()
    for category, keywords in _KEYWORDS.items():
        for kw in keywords:
            if kw in lowered:
                return category
    return "generic"


if __name__ == "__main__":
    for n in ["Alex's iPhone", "JBL Flip 5", "Galaxy Watch4", "Unknown Device", "MacBook Pro"]:
        print(f"{n:<20} -> {classify(n)}")
