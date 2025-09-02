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
    
    def format_availability_email(self, new_slots, all_evening_slots, all_slots=None):
        """Format court availability as a clean, easy-to-scan HTML email.
        all_slots: all available slots across the day (before and after 5pm)
        """
        # Precompute ids for marking new rows
        new_ids = set(f"{s['date']}_{s['time']}_{s['court']}" for s in (new_slots or []))

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
              <div style=\"background:#f8fafc;border:1px solid #eef2f7;border-radius:6px;padding:12px 14px;margin:0 0 16px 0;\">
                <div style=\"font-size:14px;color:#101828;\"><strong>Summary</strong></div>
                <div style=\"margin-top:6px;color:#344054;font-size:14px;\">New evening slots (after 5pm): <strong>{len(new_slots)}</strong></div>
                <div style=\"margin-top:2px;color:#344054;font-size:14px;\">Total evening slots (after 5pm): <strong>{len(all_evening_slots)}</strong></div>
              </div>
        """

        if new_slots:
            html += """
              <h3 style=\"margin:20px 0 8px 0;font-size:16px;color:#101828;\">New Evening Slots (after 5pm)</h3>
              <table style=\"border-collapse:collapse;width:100%;border:1px solid #e6e8eb;border-radius:6px;overflow:hidden;\">
                <thead>
                  <tr style=\"background:#f1f4f8;\">
                    <th style=\"border-bottom:1px solid #e6e8eb;padding:10px;text-align:left;font-size:13px;color:#475467;\">Date</th>
                    <th style=\"border-bottom:1px solid #e6e8eb;padding:10px;text-align:left;font-size:13px;color:#475467;\">Time</th>
                    <th style=\"border-bottom:1px solid #e6e8eb;padding:10px;text-align:left;font-size:13px;color:#475467;\">Court</th>
                  </tr>
                </thead>
                <tbody>
            """
            row_index = 0
            for s in new_slots:
                zebra = "#ffffff" if row_index % 2 == 0 else "#fbfdff"
                html += (
                    f"<tr style='background:{zebra};'>"
                    f"<td style='border-top:1px solid #eef2f7;padding:10px;font-size:14px;color:#101828;'>{s['date']}</td>"
                    f"<td style='border-top:1px solid #eef2f7;padding:10px;font-size:14px;color:#101828;'>{s['time']}</td>"
                    f"<td style='border-top:1px solid #eef2f7;padding:10px;font-size:14px;color:#101828;'>{s['court']}</td>"
                    f"</tr>"
                )
                row_index += 1
            html += """
                </tbody>
              </table>
            """

        if all_evening_slots:
            html += """
              <h3 style=\"margin:20px 0 8px 0;font-size:16px;color:#101828;\">All Evening Slots (after 5pm)</h3>
              <table style=\"border-collapse:collapse;width:100%;border:1px solid #e6e8eb;border-radius:6px;overflow:hidden;\">
                <thead>
                  <tr style=\"background:#f1f4f8;\">
                    <th style=\"border-bottom:1px solid #e6e8eb;padding:10px;text-align:left;font-size:13px;color:#475467;\">Date</th>
                    <th style=\"border-bottom:1px solid #e6e8eb;padding:10px;text-align:left;font-size:13px;color:#475467;\">Time</th>
                    <th style=\"border-bottom:1px solid #e6e8eb;padding:10px;text-align:left;font-size:13px;color:#475467;\">Court</th>
                    <th style=\"border-bottom:1px solid #e6e8eb;padding:10px;text-align:left;font-size:13px;color:#475467;\">Status</th>
                  </tr>
                </thead>
                <tbody>
            """
            row_index = 0
            for s in all_evening_slots:
                sid = f"{s['date']}_{s['time']}_{s['court']}"
                status = "New" if sid in new_ids else "Existing"
                zebra = "#ffffff" if row_index % 2 == 0 else "#fbfdff"
                badge_bg = "#16a34a" if status == "New" else "#64748b"
                html += (
                    f"<tr style='background:{zebra};'>"
                    f"<td style='border-top:1px solid #eef2f7;padding:10px;font-size:14px;color:#101828;'>{s['date']}</td>"
                    f"<td style='border-top:1px solid #eef2f7;padding:10px;font-size:14px;color:#101828;'>{s['time']}</td>"
                    f"<td style='border-top:1px solid #eef2f7;padding:10px;font-size:14px;color:#101828;'>{s['court']}</td>"
                    f"<td style='border-top:1px solid #eef2f7;padding:10px;font-size:13px;'><span style='display:inline-block;padding:2px 8px;border-radius:999px;background:{badge_bg};color:#ffffff;'>{status}</span></td>"
                    f"</tr>"
                )
                row_index += 1
            html += """
                </tbody>
              </table>

              <p style=\"margin: 18px 0;\">
                <a href=\"https://tennistowerhamlets.com/book/courts/st-johns-park\" 
                   style=\"display:inline-block;background-color:#0d6efd;color:#ffffff;padding:10px 16px;text-decoration:none;border-radius:6px;font-weight:600;\">Book Now</a>
              </p>
            """

        if all_slots:
            html += """
              <h3 style=\"margin:20px 0 8px 0;font-size:16px;color:#101828;\">All Available Slots (all day)</h3>
              <table style=\"border-collapse:collapse;width:100%;border:1px solid #e6e8eb;border-radius:6px;overflow:hidden;\">
                <thead>
                  <tr style=\"background:#f1f4f8;\">
                    <th style=\"border-bottom:1px solid #e6e8eb;padding:10px;text-align:left;font-size:13px;color:#475467;\">Date</th>
                    <th style=\"border-bottom:1px solid #e6e8eb;padding:10px;text-align:left;font-size:13px;color:#475467;\">Time</th>
                    <th style=\"border-bottom:1px solid #e6e8eb;padding:10px;text-align:left;font-size:13px;color:#475467;\">Court</th>
                  </tr>
                </thead>
                <tbody>
            """
            row_index = 0
            for s in all_slots:
                zebra = "#ffffff" if row_index % 2 == 0 else "#fbfdff"
                html += (
                    f"<tr style='background:{zebra};'>"
                    f"<td style='border-top:1px solid #eef2f7;padding:10px;font-size:14px;color:#101828;'>{s['date']}</td>"
                    f"<td style='border-top:1px solid #eef2f7;padding:10px;font-size:14px;color:#101828;'>{s['time']}</td>"
                    f"<td style='border-top:1px solid #eef2f7;padding:10px;font-size:14px;color:#101828;'>{s['court']}</td>"
                    f"</tr>"
                )
                row_index += 1
            html += """
                </tbody>
              </table>
            """

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
            
            # Filter available slots to only include times after 5pm (17:00) for initial logging
            temp_evening_slots = []
            if summary['available_slots']:
                for slot in summary['available_slots']:
                    slot_time = slot['time']
                    # Extract hour from time format (e.g., '18:00' or '8pm')
                    try:
                        if 'pm' in slot_time.lower():
                            # Handle format like '8pm'
                            hour = int(slot_time.lower().replace('pm', '').strip())
                            if hour != 12:  # Convert pm to 24-hour (except 12pm stays 12)
                                hour += 12
                        elif 'am' in slot_time.lower():
                            # Handle format like '8am'
                            hour = int(slot_time.lower().replace('am', '').strip())
                            if hour == 12:  # Convert 12am to 0
                                hour = 0
                        else:
                            # Handle format like '18:00'
                            hour = int(slot_time.split(':')[0])
                        
                        if hour >= 17:  # 5pm or later
                            temp_evening_slots.append(slot)
                    except (ValueError, IndexError):
                        continue
            
            # Log evening slots summary immediately after main summary
            if temp_evening_slots:
                self.logger.info(f"\nEVENING COURTS AVAILABLE (After 5pm): {len(temp_evening_slots)} slots")
                for slot in temp_evening_slots:
                    self.logger.info(f"   {slot['date']}: {slot['time']} ({slot['court']})")
            else:
                self.logger.info(f"\nEVENING COURTS: None available after 5pm")
            
            # Use the already filtered evening slots
            evening_slots = temp_evening_slots
            
            # Check for new evening slots
            previously_notified = self.load_notified_slots()
            current_slot_ids = set(f"{slot['date']}_{slot['time']}_{slot['court']}" for slot in evening_slots)
            new_slot_ids = current_slot_ids - previously_notified
            
            # Get new slots objects
            new_evening_slots = [slot for slot in evening_slots 
                               if f"{slot['date']}_{slot['time']}_{slot['court']}" in new_slot_ids]
            
            # Always log new evening courts section
            if new_evening_slots:
                self.logger.info(f"\nNEW EVENING COURTS (After 5pm): {len(new_evening_slots)} new slots found!")
                for slot in new_evening_slots:
                    self.logger.info(f"   NEW: {slot['date']}: {slot['time']} ({slot['court']})")
            else:
                self.logger.info(f"\nNEW EVENING COURTS (After 5pm): No new slots since last check")
            
            # Update notified slots to current state (always save the current slots)
            self.save_notified_slots(evening_slots)
            
            # Only send notification if there are new courts available after 5pm
            if new_evening_slots:
                subject = f"{len(new_evening_slots)} New Tennis Courts Available After 5pm at St Johns Park!"
                body = self.format_availability_email(new_evening_slots, evening_slots, summary.get('available_slots'))
                self.send_notification(subject, body)
                self.logger.info(f"Email notification sent for {len(new_evening_slots)} new evening courts")
            else:
                if evening_slots:
                    self.logger.info(f"No email sent - evening courts available but no new ones ({len(evening_slots)} total slots)")
                elif summary['available_slots']:
                    self.logger.info(f"No email sent - courts available but none after 5pm ({len(summary['available_slots'])} total slots)")
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
