# 🎾 St Johns Park Tennis Court Monitor

Automated monitoring system for tennis court availability at St Johns Park, Tower Hamlets. Runs 24/7 on GitHub Actions and sends email notifications when courts become available.

## Features

- ✅ **24/7 Monitoring** - Runs every 30 minutes from 6 AM to 11 PM UK time
- ✅ **Email Notifications** - Get alerted when courts become available
- ✅ **Comprehensive Checking** - Monitors all time slots, not just evenings
- ✅ **Mac-Independent** - Runs on GitHub's servers, no need to keep your computer on
- ✅ **Free** - Uses GitHub Actions free tier (2,000 minutes/month)

## Quick Start

### 1. Fork/Clone this Repository

```bash
git clone https://github.com/YOUR_USERNAME/tennis_bot_st_johns
cd tennis_bot_st_johns
```

### 2. Set up Email Notifications

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**

Add these secrets:

| Secret Name | Description | Example |
|------------|-------------|---------|
| `SMTP_SERVER` | Email SMTP server | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` |
| `EMAIL_USER` | Your email address | `your-email@gmail.com` |
| `EMAIL_PASSWORD` | Your email password/app password | `your-app-password` |
| `NOTIFICATION_EMAIL` | Where to send notifications | `your-phone@gmail.com` |

#### For Gmail Users:
1. Enable 2-factor authentication
2. Generate an App Password: [Google App Passwords](https://myaccount.google.com/apppasswords)
3. Use the app password (not your regular password) for `EMAIL_PASSWORD`

### 3. Enable GitHub Actions

1. Go to **Actions** tab in your repository
2. Click **"I understand my workflows, go ahead and enable them"**
3. The workflow will start running automatically

### 4. Manual Testing

You can trigger a manual check:
1. Go to **Actions** → **Tennis Court Availability Monitor**
2. Click **"Run workflow"** → **"Run workflow"**

## How It Works

### Monitoring Schedule
- Runs every **30 minutes** from 6 AM to 11 PM UK time
- Checks all 7 days in advance
- Monitors both Court 1 and Court 2
- Covers all time slots from 7 AM to 9 PM

### What Gets Monitored
- ✅ **Available slots** - Free courts you can book
- 🔒 **Booked slots** - Already taken
- 🏫 **Session slots** - Group coaching sessions
- ❌ **Closed days** - When facility is closed

### Notifications
You'll get an email when:
- **Courts become available** (immediate notification)
- **Errors occur** (so you know if monitoring stops working)

Example notification:
```
🎾 2 Tennis Courts Available at St Johns Park!

🎉 Available Courts Found!
• 2025-07-27 at 7am - court_2  
• 2025-07-28 at 7am - court_2

🔗 Book Now
```

## Local Development

### Run Locally
```bash
# Set up virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run single check
python st_johns_court_checker.py

# Run GitHub Actions version locally
python github_runner.py
```

### Debug Mode
Uncomment the HTML debug lines in `st_johns_court_checker.py` to save website HTML for analysis.

## File Structure

```
tennis_bot_st_johns/
├── st_johns_court_checker.py    # Main court checking logic
├── github_runner.py             # GitHub Actions runner with notifications
├── requirements.txt             # Python dependencies
├── .github/workflows/
│   └── court_monitor.yml        # GitHub Actions workflow
└── README.md                    # This file
```

## Configuration

### Change Check Frequency
Edit `.github/workflows/court_monitor.yml`:
```yaml
schedule:
  - cron: '*/15 5-22 * * *'  # Every 15 minutes instead of 30
```

### Customize Preferred Times
Modify `github_runner.py` to filter for specific times:
```python
# Only notify for evening slots
preferred_times = ['6pm', '7pm', '8pm', '9pm']
evening_slots = [slot for slot in summary['available_slots'] 
                if slot['time'] in preferred_times]
```

## Troubleshooting

### Email Not Working?
1. Check your GitHub Secrets are set correctly
2. For Gmail: Make sure you're using an App Password, not your regular password
3. Check the Actions logs for error messages

### No Notifications?
The script only sends emails when courts are **available**. St Johns Park is very popular, so available slots are rare (mostly early morning).

### GitHub Actions Not Running?
1. Make sure the repository is not a fork (forks have limited Actions by default)
2. Check the Actions tab for any error messages
3. Ensure you've enabled workflows in the Actions tab

## Cost

This solution is **completely free** using GitHub Actions:
- 2,000 minutes/month free tier
- Each check takes ~2 minutes
- 30-minute intervals = ~1,440 minutes/month
- Well within the free limit!

## Legal & Ethics

This tool:
- ✅ Uses public booking data responsibly
- ✅ Includes delays between requests (1-second intervals)
- ✅ Only checks availability, doesn't auto-book
- ✅ Respects the website's terms of service

## Support

Having issues? Check:
1. GitHub Actions logs in the **Actions** tab
2. Email spam folder for notifications
3. Repository **Issues** tab for known problems

---

**Happy court hunting! 🎾**