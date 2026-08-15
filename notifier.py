"""
notifier.py

Sends a desktop notification when a "watched" device enters or
leaves range. Uses `plyer` if installed (cross-platform), and falls
back to printing in the terminal if plyer isn't available or the OS
notification system can't be reached (e.g. this sandboxed
environment).
"""

def notify(title: str, message: str):
    try:
        from plyer import notification
        notification.notify(title=title, message=message, timeout=5)
    except Exception:
        # Fallback: plyer not installed, or no OS notification backend
        # available in this environment. Always at least print it.
        print(f"[NOTIFICATION] {title}: {message}")


if __name__ == "__main__":
    notify("R.A.D.A.R", "Test notification — watched device entered range.")
