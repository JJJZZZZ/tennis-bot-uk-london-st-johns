# 🎾 St Johns Park Tennis Court Monitor

**Goal:** Automatically monitor tennis court availability at St Johns Park (Tower Hamlets) and send email notifications when evening courts (after 5pm) become available.

## What This Script Does

- **Monitors:** St Johns Park tennis courts every 30 minutes (6 AM - 1 AM UK time)
- **Checks:** All available time slots across 7 days in advance
- **Filters:** Only notifies for courts available after 5pm
- **Smart Notifications:** Only sends emails for genuinely new slots (prevents spam)
- **Runs:** Automatically on GitHub Actions (free, no computer needed)

## Email Notifications

The email is designed to be easy to scan at a glance:

- Header: shows the check time (UTC)
- New Evening Slots (after 5pm): grouped by day cards labeled with `YYYY-MM-DD (Weekday)` and a count badge; each slot appears as a compact pill like `18:00 • Court 2`
- All Evening Slots (after 5pm): also grouped by day with a total count and a “new” count; newly found slots are highlighted
- All Available Slots: grouped by day for the entire day (not just evenings); clean pill layout

Notes:
- Days are labelled with the weekday (e.g., `2025-09-16 (Tuesday)`).
- The previous summary box has been removed to keep the focus on the grouped sections.

## Setup

1. **Fork this repository**
2. **Add GitHub Secrets** (Settings → Secrets → Actions):
   - `EMAIL_USER` - Your Gmail address
   - `EMAIL_PASSWORD` - Gmail app password
   - `NOTIFICATION_EMAIL` - Where to send alerts
   - `SMTP_SERVER` - `smtp.gmail.com`
   - `SMTP_PORT` - `587`
3. **Enable GitHub Actions** (Actions tab → Enable workflows)

## Triggering Runs

- Scheduled: Runs automatically every 30 minutes between 6 AM and 1 AM UK time.
- Manual (GitHub UI):
  - Go to the repo → Actions → “Tennis Court Monitor” → “Run workflow”.
- Manual (GitHub CLI):
  - `gh workflow run .github/workflows/tennis_monitor.yml`
  - Or run by name: `gh workflow run "Tennis Court Monitor"`

## Files

- `github_runner.py` - Main script with smart email logic
- `st_johns_court_checker.py` - Court availability checker
- `.github/workflows/tennis_monitor.yml` - Automated schedule

## What’s New

- Weekday labels next to every date in the email
- Grouped-by-day cards with pill-style times for all sections
- New evening slots highlighted and per-day new counts
- Removed the summary card; simplified section titles

---

**Simple, effective, free tennis court monitoring! 🎾**
