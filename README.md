# 🎾 St Johns Park Tennis Court Monitor

**Goal:** Automatically monitor tennis court availability at St Johns Park (Tower Hamlets) and send email notifications when evening courts (after 5pm) become available.

## What This Script Does

- **Monitors:** St Johns Park tennis courts every 30 minutes (6 AM - 1 AM UK time)
- **Checks:** All available time slots across 7 days in advance
- **Filters:** Only notifies for courts available after 5pm
- **Smart Notifications:** Only sends emails for genuinely new slots (prevents spam)
- **Runs:** Automatically on GitHub Actions (free, no computer needed)

## Email Notifications

You'll receive emails when **new** evening courts become available:

```
🎾 1 New Tennis Courts Available After 5pm at St Johns Park!

🆕 New Courts Available After 5pm!
• 2025-08-27 at 17:00 - Court 3

🌅 All Available Courts After 5pm:
• 2025-08-26 at 18:00 - Court 1
• 2025-08-27 at 17:00 - Court 3 [NEW]

🔗 Book Now
```

## Setup

1. **Fork this repository**
2. **Add GitHub Secrets** (Settings → Secrets → Actions):
   - `EMAIL_USER` - Your Gmail address
   - `EMAIL_PASSWORD` - Gmail app password
   - `NOTIFICATION_EMAIL` - Where to send alerts
   - `SMTP_SERVER` - `smtp.gmail.com`
   - `SMTP_PORT` - `587`
3. **Enable GitHub Actions** (Actions tab → Enable workflows)

## Files

- `github_runner.py` - Main script with smart email logic
- `st_johns_court_checker.py` - Court availability checker
- `.github/workflows/tennis_monitor.yml` - Automated schedule

---

**Simple, effective, free tennis court monitoring! 🎾**