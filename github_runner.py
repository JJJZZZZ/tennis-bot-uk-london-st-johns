#!/usr/bin/env python3
"""
GitHub Actions Runner for St Johns Park Tennis Court Availability Monitor
Designed to run in GitHub Actions environment with email notifications
"""

import os
import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from st_johns_court_checker import StJohnsParkChecker

class GitHubCourtMonitor:
    def __init__(self):
        self.checker = StJohnsParkChecker()
        
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
    
    def format_availability_email(self, summary):
        """Format court availability as HTML email"""
        html = f"""
        <html>
        <head></head>
        <body>
            <h2>🎾 St Johns Park Tennis Court Update</h2>
            <p><strong>Check Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        """
        
        if summary['available_slots']:
            html += f"""
            <h3>🎉 Available Courts Found!</h3>
            <ul>
            """
            for slot in summary['available_slots']:
                html += f"<li><strong>{slot['date']}</strong> at <strong>{slot['time']}</strong> - {slot['court']}</li>"
            html += "</ul>"
            
            html += f"""
            <p><a href="https://tennistowerhamlets.com/book/courts/st-johns-park" 
               style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
               🔗 Book Now</a></p>
            """
        else:
            html += "<h3>❌ No Available Courts</h3>"
            html += f"<p>All courts are currently booked. Checked {len(summary['booked_slots'])} slots.</p>"
        
        html += f"""
            <h3>📊 Summary</h3>
            <ul>
                <li>Available: {len(summary['available_slots'])}</li>
                <li>Booked: {len(summary['booked_slots'])}</li>
                <li>Sessions: {len(summary['session_slots'])}</li>
                <li>Closed Days: {len(summary['closed_days'])}</li>
            </ul>
            
            <hr>
            <p><small>Automated check via GitHub Actions</small></p>
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
            
            # Log results
            self.logger.info(f"Check completed - Available: {len(summary['available_slots'])}, "
                           f"Booked: {len(summary['booked_slots'])}, "
                           f"Sessions: {len(summary['session_slots'])}")
            
            # Filter available slots to only include times after 5pm (17:00)
            evening_slots = []
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
                            evening_slots.append(slot)
                    except (ValueError, IndexError):
                        # If time format is unexpected, skip this slot
                        self.logger.warning(f"Unexpected time format: {slot_time}")
                        continue
            
            # Only send notification if courts are available after 5pm
            if evening_slots:
                subject = f"🎾 {len(evening_slots)} Tennis Courts Available After 5pm at St Johns Park!"
                # Update summary to only include evening slots for email
                evening_summary = summary.copy()
                evening_summary['available_slots'] = evening_slots
                body = self.format_availability_email(evening_summary)
                self.send_notification(subject, body)
                
                # Also log available evening slots
                self.logger.info("AVAILABLE EVENING COURTS FOUND (after 5pm):")
                for slot in evening_slots:
                    self.logger.info(f"  {slot['date']} at {slot['time']} - {slot['court']}")
            else:
                if summary['available_slots']:
                    self.logger.info(f"Courts available but none after 5pm ({len(summary['available_slots'])} total slots)")
                else:
                    self.logger.info("No available courts found")
                # Optionally send daily summary (uncomment if you want daily updates)
                # if datetime.now().hour == 20:  # 8 PM UTC (9 PM UK time)
                #     subject = "📊 Daily Tennis Court Summary - St Johns Park"
                #     body = self.format_availability_email(summary)
                #     self.send_notification(subject, body)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error during court check: {e}")
            # Send error notification
            if self.email_user and self.notification_email:
                error_subject = "⚠️ Tennis Court Monitor Error"
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