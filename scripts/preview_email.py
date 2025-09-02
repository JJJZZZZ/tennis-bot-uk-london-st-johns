#!/usr/bin/env python3
"""
Generate a local HTML preview of the email content with mock data.
Output: preview_email.html in repo root.
"""

from pathlib import Path
import sys, os

# Ensure repo root is importable when running from scripts/
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from github_runner import GitHubCourtMonitor


def main():
    monitor = GitHubCourtMonitor()

    new_slots = [
        {"date": "2025-09-05", "time": "17:30", "court": "Court 1"},
        {"date": "2025-09-05", "time": "18:00", "court": "Court 3"},
    ]

    all_evening_slots = [
        {"date": "2025-09-05", "time": "17:30", "court": "Court 1"},
        {"date": "2025-09-05", "time": "18:00", "court": "Court 3"},
        {"date": "2025-09-05", "time": "19:00", "court": "Court 2"},
        {"date": "2025-09-06", "time": "20:00", "court": "Court 4"},
    ]

    html = monitor.format_availability_email(new_slots, all_evening_slots, new_slots + all_evening_slots)

    out_path = Path("preview_email.html")
    out_path.write_text(html, encoding="utf-8")
    print(f"Wrote {out_path.resolve()}")


if __name__ == "__main__":
    main()
