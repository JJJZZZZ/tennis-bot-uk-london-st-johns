#!/usr/bin/env python3
"""
GitHub Actions Runner for St Johns Park Tennis Court Availability Monitor
Designed to run in GitHub Actions environment with email notifications
"""

import os
import json
import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from st_johns_court_checker import StJohnsParkChecker

class GitHubCourtMonitor:
    def __init__(self):
        self.checker = StJohnsParkChecker()
        self.state_file = 'notified_slots.json'
        
        # Email configuration from environment variables
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.notification_email = os.getenv('NOTIFICATION_EMAIL')
        
        # Set up logging to file for GitHub Actions artifact
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('court_check.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def is_weekend(self, date_str: str) -> bool:
        """Check if a date is Saturday or Sunday"""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            # weekday() returns 0=Monday, 6=Sunday
            return date_obj.weekday() in [5, 6]  # 5=Saturday, 6=Sunday
        except Exception:
            return False

    def get_time_range_for_date(self, date_str: str) -> tuple:
        """
        Get the time range filter for a given date.
        Returns: (min_hour, max_hour, description)
        """
        if self.is_weekend(date_str):
            return (9, 22, "Available (9am-10pm)")
        else:
            return (17, 24, "Evening (after 5pm)")

    def parse_time_to_hour(self, time_str: str) -> int:
        """
        Extract hour from various time formats (e.g., '18:00', '8pm', '8am')
        Returns hour in 24-hour format, or -1 if parsing fails
        """
        try:
            time_lower = time_str.lower().strip()

            if 'pm' in time_lower:
                # Handle format like '8pm'
                hour = int(time_lower.replace('pm', '').strip())
                if hour != 12:  # Convert pm to 24-hour (except 12pm stays 12)
                    hour += 12
            elif 'am' in time_lower:
                # Handle format like '8am'
                hour = int(time_lower.replace('am', '').strip())
                if hour == 12:  # Convert 12am to 0
                    hour = 0
            else:
                # Handle format like '18:00'
                hour = int(time_lower.split(':')[0])

            return hour
        except (ValueError, IndexError):
            return -1

    def send_notification(self, subject: str, body: str):
        """Send email notification about court availability"""
        if not all([self.email_user, self.email_password, self.notification_email]):
            self.logger.warning("Email configuration incomplete - skipping notification")
            return False
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = self.notification_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            text = msg.as_string()
            server.sendmail(self.email_user, self.notification_email, text)
            server.quit()
            
            self.logger.info(f"Notification sent successfully to {self.notification_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
            return False
    
    def load_notified_slots(self):
        """Load previously notified slots from file"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    return set(json.load(f))
        except Exception as e:
            self.logger.warning(f"Could not load notified slots: {e}")
        return set()
    
    def save_notified_slots(self, slots):
        """Save currently notified slots to file"""
        try:
            slot_ids = [f"{slot['date']}_{slot['time']}_{slot['court']}" for slot in slots]
            with open(self.state_file, 'w') as f:
                json.dump(slot_ids, f)
        except Exception as e:
            self.logger.error(f"Could not save notified slots: {e}")
    
    def format_availability_email(self, new_slots, all_filtered_slots, all_slots=None):
        """Format court availability as a clean, easy-to-scan HTML email.
        all_filtered_slots: filtered slots based on day type (weekday: after 5pm, weekend: 9am-10pm)
        all_slots: all available slots across the day (before and after filtering)
        """
        # Precompute ids for marking new rows
        new_ids = set(f"{s['date']}_{s['time']}_{s['court']}" for s in (new_slots or []))

        # Helper to determine section title based on day types in the slots
        def get_section_title(slots, prefix="Available"):
            if not slots:
                return f"{prefix} Slots"
            has_weekday = any(not self.is_weekend(s['date']) for s in slots)
            has_weekend = any(self.is_weekend(s['date']) for s in slots)
            if has_weekday and has_weekend:
                return f"{prefix} Slots"
            elif has_weekend:
                return f"{prefix} Slots (Weekend 9am-10pm)"
            else:
                return f"{prefix} Slots (Weekday After 5pm)"

        # Helper to get weekday name for a YYYY-MM-DD date string
        def weekday_name(date_str: str) -> str:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d').strftime('%A')
            except Exception:
                return ''

        # Helper to create a numeric sort key (minutes since midnight) from various time formats
        def time_sort_key(t: str) -> int:
            try:
                tl = t.strip().lower()
                is_am = 'am' in tl
                is_pm = 'pm' in tl
                tl = tl.replace('am', '').replace('pm', '').strip()
                hour = 0
                minute = 0
                if ':' in tl:
                    parts = tl.split(':')
                    hour = int(parts[0])
                    minute = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                else:
                    hour = int(''.join(ch for ch in tl if ch.isdigit())) if any(ch.isdigit() for ch in tl) else 0
                if is_pm and hour != 12:
                    hour += 12
                if is_am and hour == 12:
                    hour = 0
                return hour * 60 + minute
            except Exception:
                return 0

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')

        html = f"""
        <html>
        <head>
            <meta charset=\"UTF-8\" />
        </head>
        <body style=\"margin:0;padding:24px;background-color:#f5f7fb;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif;\">
          <div style=\"max-width:640px;margin:0 auto;background:#ffffff;border:1px solid #e6e8eb;border-radius:8px;box-shadow:0 2px 6px rgba(16,24,40,.08);overflow:hidden;\">
            <div style=\"background:#0d6efd;color:#ffffff;padding:16px 20px;\">
              <h2 style=\"margin:0;font-size:20px;\">St Johns Park Tennis Court Availability</h2>
              <div style=\"margin-top:4px;font-size:12px;opacity:.95;\">Checked at: {timestamp}</div>
            </div>
            <div style=\"padding:20px;\">
        """

        if new_slots:
            new_section_title = get_section_title(new_slots, "New")
            html += f"""
              <h3 style=\"margin:20px 0 8px 0;font-size:16px;color:#101828;\">{new_section_title}</h3>
            """
            # Group new evening slots by date
            ns_by_date = {}
            for s in new_slots:
                d = s.get('date')
                if not d:
                    continue
                ns_by_date.setdefault(d, []).append(s)

            for d in sorted(ns_by_date.keys()):
                slots = sorted(ns_by_date[d], key=lambda x: time_sort_key(x.get('time', '0:00')))
                count = len(slots)
                dow = weekday_name(d)
                html += (
                    f"<div style='border:1px solid #e6e8eb;border-radius:8px;margin:10px 0;overflow:hidden;'>"
                    f"<div style='background:#f8fafc;padding:10px 12px;border-bottom:1px solid #eef2f7;display:flex;align-items:center;justify-content:space-between;'>"
                    f"<div style='font-size:14px;color:#101828;font-weight:600;'>{d} ({dow})</div>"
                    f"<div style='font-size:12px;color:#475467;background:#e6f4ff;border:1px solid #cfe5ff;border-radius:999px;padding:2px 8px;'>"
                    f"{count} slot{'s' if count != 1 else ''}</div>"
                    f"</div>"
                    f"<div style='padding:10px 12px;'>"
                )

                for s in slots:
                    court_label = s['court'].replace('_', ' ').title()
                    html += (
                        f"<span style='display:inline-block;margin:4px 6px 0 0;padding:6px 10px;border:1px solid #e6e8eb;border-radius:999px;background:#ffffff;font-size:13px;color:#101828;'>"
                        f"{s['time']} • {court_label}"
                        f"</span>"
                    )

                html += "</div></div>"

        if all_filtered_slots:
            all_section_title = get_section_title(all_filtered_slots, "All")
            html += f"""
              <h3 style=\"margin:20px 0 8px 0;font-size:16px;color:#101828;\">{all_section_title}</h3>
            """
            # Group all filtered slots by date
            es_by_date = {}
            for s in all_filtered_slots:
                d = s.get('date')
                if not d:
                    continue
                es_by_date.setdefault(d, []).append(s)

            for d in sorted(es_by_date.keys()):
                slots = sorted(es_by_date[d], key=lambda x: time_sort_key(x.get('time', '0:00')))
                count = len(slots)
                dow = weekday_name(d)
                # Count new items for this day
                new_count = sum(1 for s in slots if f"{s['date']}_{s['time']}_{s['court']}" in new_ids)
                html += (
                    f"<div style='border:1px solid #e6e8eb;border-radius:8px;margin:10px 0;overflow:hidden;'>"
                    f"<div style='background:#f8fafc;padding:10px 12px;border-bottom:1px solid #eef2f7;display:flex;align-items:center;justify-content:space-between;'>"
                    f"<div style='font-size:14px;color:#101828;font-weight:600;'>{d} ({dow})</div>"
                    f"<div>"
                    f"<span style='display:inline-block;margin-left:6px;font-size:12px;color:#475467;background:#e6f4ff;border:1px solid #cfe5ff;border-radius:999px;padding:2px 8px;'>{count} slot{'s' if count != 1 else ''}</span>"
                    f"<span style='display:inline-block;margin-left:6px;font-size:12px;color:#155e2b;background:#dcfce7;border:1px solid #bbf7d0;border-radius:999px;padding:2px 8px;'>{new_count} new</span>"
                    f"</div>"
                    f"</div>"
                    f"<div style='padding:10px 12px;'>"
                )

                for s in slots:
                    sid = f"{s['date']}_{s['time']}_{s['court']}"
                    is_new = sid in new_ids
                    court_label = s['court'].replace('_', ' ').title()
                    pill_bg = '#e8f7ee' if is_new else '#ffffff'
                    pill_border = '#86efac' if is_new else '#e6e8eb'
                    pill_color = '#065f46' if is_new else '#101828'
                    html += (
                        f"<span style='display:inline-block;margin:4px 6px 0 0;padding:6px 10px;border:1px solid {pill_border};border-radius:999px;background:{pill_bg};font-size:13px;color:{pill_color};'>"
                        f"{s['time']} • {court_label}"
                        f"</span>"
                    )

                html += "</div></div>"

            html += """
              <p style=\"margin: 18px 0;\">
                <a href=\"https://tennistowerhamlets.com/book/courts/st-johns-park\" 
                   style=\"display:inline-block;background-color:#0d6efd;color:#ffffff;padding:10px 16px;text-decoration:none;border-radius:6px;font-weight:600;\">Book Now</a>
              </p>
            """

        if all_slots:
            html += """
              <h3 style=\"margin:20px 0 8px 0;font-size:16px;color:#101828;\">All Available Slots</h3>
            """
            # Group slots by date
            by_date = {}
            for s in all_slots:
                d = s.get('date')
                if not d:
                    continue
                by_date.setdefault(d, []).append(s)

            for d in sorted(by_date.keys()):
                slots = sorted(by_date[d], key=lambda x: time_sort_key(x.get('time', '0:00')))
                count = len(slots)
                dow = weekday_name(d)
                html += (
                    f"<div style='border:1px solid #e6e8eb;border-radius:8px;margin:10px 0;overflow:hidden;'>"
                    f"<div style='background:#f8fafc;padding:10px 12px;border-bottom:1px solid #eef2f7;display:flex;align-items:center;justify-content:space-between;'>"
                    f"<div style='font-size:14px;color:#101828;font-weight:600;'>{d} ({dow})</div>"
                    f"<div style='font-size:12px;color:#475467;background:#e6f4ff;border:1px solid #cfe5ff;border-radius:999px;padding:2px 8px;'>"
                    f"{count} slot{'s' if count != 1 else ''}</div>"
                    f"</div>"
                    f"<div style='padding:10px 12px;'>"
                )

                # Render each slot as a pill for easy scanning
                for s in slots:
                    court_label = s['court'].replace('_', ' ').title()
                    html += (
                        f"<span style='display:inline-block;margin:4px 6px 0 0;padding:6px 10px;border:1px solid #e6e8eb;border-radius:999px;background:#ffffff;font-size:13px;color:#101828;'>"
                        f"{s['time']} • {court_label}"
                        f"</span>"
                    )

                html += "</div></div>"

        html += """
            </div>
            <div style=\"padding:12px 20px;border-top:1px solid #e6e8eb;background:#fafbfc;color:#667085;font-size:12px;\">
              Automated check via GitHub Actions
            </div>
          </div>
        </body>
        </html>
        """
        return html
    
    def run_check(self):
        """Main function to check courts and send notifications"""
        self.logger.info("Starting automated court availability check")
        
        try:
            # Initialize session
            if not self.checker.initialize_session():
                self.logger.error("Failed to initialize session")
                return False
            
            # Get comprehensive summary
            summary = self.checker.get_all_slots_summary()
            
            # Log clean summary report
            summary_report = self.checker.format_summary_report(summary)
            self.logger.info(f"Court check completed:\n{summary_report}")
            
            # Filter available slots based on day type (weekday: after 5pm, weekend: 9am-10pm)
            temp_filtered_slots = []
            if summary['available_slots']:
                for slot in summary['available_slots']:
                    slot_date = slot['date']
                    slot_time = slot['time']

                    # Get time range for this specific date (weekday vs weekend)
                    min_hour, max_hour, _ = self.get_time_range_for_date(slot_date)

                    # Parse the hour from the slot time
                    hour = self.parse_time_to_hour(slot_time)

                    # Check if hour is within the valid range for this day type
                    if hour != -1 and min_hour <= hour < max_hour:
                        temp_filtered_slots.append(slot)
            
            # Log filtered slots summary immediately after main summary
            if temp_filtered_slots:
                # Group by day type for clearer logging
                weekday_slots = [s for s in temp_filtered_slots if not self.is_weekend(s['date'])]
                weekend_slots = [s for s in temp_filtered_slots if self.is_weekend(s['date'])]

                if weekday_slots:
                    self.logger.info(f"\nWEEKDAY COURTS AVAILABLE (After 5pm): {len(weekday_slots)} slots")
                    for slot in weekday_slots:
                        self.logger.info(f"   {slot['date']}: {slot['time']} ({slot['court']})")

                if weekend_slots:
                    self.logger.info(f"\nWEEKEND COURTS AVAILABLE (9am-10pm): {len(weekend_slots)} slots")
                    for slot in weekend_slots:
                        self.logger.info(f"   {slot['date']}: {slot['time']} ({slot['court']})")
            else:
                self.logger.info(f"\nFILTERED COURTS: None available in target time ranges")

            # Use the already filtered slots
            filtered_slots = temp_filtered_slots
            
            # Check for new slots (weekday evening or weekend daytime)
            previously_notified = self.load_notified_slots()
            current_slot_ids = set(f"{slot['date']}_{slot['time']}_{slot['court']}" for slot in filtered_slots)
            new_slot_ids = current_slot_ids - previously_notified

            # Get new slots objects
            new_filtered_slots = [slot for slot in filtered_slots
                               if f"{slot['date']}_{slot['time']}_{slot['court']}" in new_slot_ids]

            # Always log new courts section
            if new_filtered_slots:
                weekday_new = [s for s in new_filtered_slots if not self.is_weekend(s['date'])]
                weekend_new = [s for s in new_filtered_slots if self.is_weekend(s['date'])]

                self.logger.info(f"\nNEW COURTS FOUND: {len(new_filtered_slots)} new slots!")
                if weekday_new:
                    self.logger.info(f"  Weekday (after 5pm): {len(weekday_new)} slots")
                    for slot in weekday_new:
                        self.logger.info(f"     NEW: {slot['date']}: {slot['time']} ({slot['court']})")
                if weekend_new:
                    self.logger.info(f"  Weekend (9am-10pm): {len(weekend_new)} slots")
                    for slot in weekend_new:
                        self.logger.info(f"     NEW: {slot['date']}: {slot['time']} ({slot['court']})")
            else:
                self.logger.info(f"\nNEW COURTS: No new slots since last check")

            # Update notified slots to current state (always save the current slots)
            self.save_notified_slots(filtered_slots)
            
            # Only send notification if there are new courts available
            if new_filtered_slots:
                # Generate dynamic subject based on day types
                weekday_count = len([s for s in new_filtered_slots if not self.is_weekend(s['date'])])
                weekend_count = len([s for s in new_filtered_slots if self.is_weekend(s['date'])])

                if weekday_count > 0 and weekend_count > 0:
                    subject = f"{len(new_filtered_slots)} New Tennis Courts Available at St Johns Park!"
                elif weekend_count > 0:
                    subject = f"{len(new_filtered_slots)} New Tennis Courts Available (Weekend 9am-10pm) at St Johns Park!"
                else:
                    subject = f"{len(new_filtered_slots)} New Tennis Courts Available (After 5pm) at St Johns Park!"

                body = self.format_availability_email(new_filtered_slots, filtered_slots, summary.get('available_slots'))
                self.send_notification(subject, body)
                self.logger.info(f"Email notification sent for {len(new_filtered_slots)} new courts")
            else:
                if filtered_slots:
                    self.logger.info(f"No email sent - courts available but no new ones ({len(filtered_slots)} total slots)")
                elif summary['available_slots']:
                    self.logger.info(f"No email sent - courts available but none in target time ranges ({len(summary['available_slots'])} total slots)")
                else:
                    self.logger.info("No email sent - no available courts found")
                # Optionally send daily summary (uncomment if you want daily updates)
                # if datetime.now().hour == 20:  # 8 PM UTC (9 PM UK time)
                #     subject = "Daily Tennis Court Summary - St Johns Park"
                #     body = self.format_availability_email(summary)
                #     self.send_notification(subject, body)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error during court check: {e}")
            # Send error notification
            if self.email_user and self.notification_email:
                error_subject = "Tennis Court Monitor Error"
                error_body = f"""
                <html><body>
                <h2>Tennis Court Monitor Error</h2>
                <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                <p><strong>Error:</strong> {str(e)}</p>
                </body></html>
                """
                self.send_notification(error_subject, error_body)
            return False

if __name__ == "__main__":
    monitor = GitHubCourtMonitor()
    success = monitor.run_check()
    
    if not success:
        exit(1)  # Exit with error code for GitHub Actions
    
    print("Court check completed successfully")
