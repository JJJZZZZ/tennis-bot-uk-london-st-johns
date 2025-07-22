#!/usr/bin/env python3
"""
St Johns Park Tennis Court Availability Checker
Scrapes the Courtside booking system to check court availability
"""

import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import logging
import json
from typing import Dict, List, Optional

class StJohnsParkChecker:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://tennistowerhamlets.com"
        self.booking_url = f"{self.base_url}/book/courts/st-johns-park"
        
        # Set up headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
    def initialize_session(self) -> bool:
        """Initialize session by visiting the main page to get cookies"""
        try:
            response = self.session.get(self.booking_url)
            response.raise_for_status()
            self.logger.info("Session initialized successfully")
            return True
        except requests.RequestException as e:
            self.logger.error(f"Failed to initialize session: {e}")
            return False
    
    def get_available_dates(self) -> List[str]:
        """Get list of available booking dates (7 days ahead)"""
        dates = []
        today = datetime.now()
        
        for i in range(7):
            date = today + timedelta(days=i)
            dates.append(date.strftime('%Y-%m-%d'))
            
        return dates
    
    def check_court_availability(self, date: str, time_slots: List[str] = None) -> Dict:
        """
        Check court availability for a specific date
        
        Args:
            date: Date in YYYY-MM-DD format
            time_slots: List of time slots to check (e.g., ['09:00', '10:00'])
        
        Returns:
            Dict with availability information
        """
        if time_slots is None:
            time_slots = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00']
        
        availability = {
            'date': date,
            'courts': {},
            'error': None
        }
        
        try:
            # Build URL with specific date
            if date != datetime.now().strftime('%Y-%m-%d'):
                url = f"{self.booking_url}/{date}#book"
            else:
                url = f"{self.booking_url}#book"
            
            # Make request to booking page
            response = self.session.get(url)
            response.raise_for_status()
            self.logger.info(f"Requesting URL: {url}")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Optional: Save HTML for debugging (uncomment if needed)
            # with open(f'debug_html_{date}.html', 'w', encoding='utf-8') as f:
            #     f.write(soup.prettify())
            
            # Look for date picker or form elements
            date_inputs = soup.find_all('input', {'type': 'date'})
            time_selects = soup.find_all('select', class_=lambda x: x and 'time' in x.lower())
            
            self.logger.info(f"Found {len(date_inputs)} date inputs and {len(time_selects)} time selects")
            
            # Check for AJAX endpoints in script tags
            scripts = soup.find_all('script')
            ajax_count = 0
            for script in scripts:
                if script.string and ('ajax' in script.string.lower() or 'api' in script.string.lower()):
                    ajax_count += 1
                    self.logger.info("Found potential AJAX endpoint in script")
            
            self.logger.info(f"Found {ajax_count} scripts with AJAX/API content")
            
            # Check if venue is closed
            closed_element = soup.find('p', class_='closed')
            if closed_element:
                self.logger.info(f"Venue is closed on {date}")
                availability['status'] = 'closed'
                availability['message'] = closed_element.get_text(strip=True)
                return availability
            
            # Look for court availability table
            availability_div = soup.find('div', class_='availability')
            if availability_div:
                # Find the booking table
                table = availability_div.find('table')
                if table:
                    rows = table.find_all('tr')
                    
                    court_data = {
                        'court_1': {'available_times': [], 'booked_times': [], 'session_times': []},
                        'court_2': {'available_times': [], 'booked_times': [], 'session_times': []}
                    }
                    
                    for row in rows:
                        # Get time from th element
                        time_cell = row.find('th', class_='time')
                        if not time_cell:
                            continue
                            
                        time_str = time_cell.get_text(strip=True)
                        
                        # Get court cells
                        court_cells = row.find_all('label', class_='court')
                        
                        for i, court_cell in enumerate(court_cells):
                            court_name = f'court_{i + 1}'
                            
                            # Check the button class to determine status
                            button = court_cell.find('span', class_='button')
                            if button:
                                if 'available' in button.get('class', []):
                                    court_data[court_name]['available_times'].append(time_str)
                                elif 'booked' in button.get('class', []):
                                    court_data[court_name]['booked_times'].append(time_str)
                                elif 'session' in button.get('class', []):
                                    court_data[court_name]['session_times'].append(time_str)
                    
                    availability['courts'] = court_data
                    
                    total_available = sum(len(court['available_times']) for court in court_data.values())
                    total_booked = sum(len(court['booked_times']) for court in court_data.values())
                    total_sessions = sum(len(court['session_times']) for court in court_data.values())
                    
                    self.logger.info(f"Parsed table: {total_available} available, {total_booked} booked, {total_sessions} sessions")
                else:
                    self.logger.info("No booking table found in availability div")
            else:
                self.logger.info("No availability div found")
            
            availability['status'] = 'open'
            
            self.logger.info(f"Checked availability for {date}")
            
        except requests.RequestException as e:
            self.logger.error(f"Request failed for date {date}: {e}")
            availability['error'] = str(e)
            
        return availability
    
    def find_available_slots(self, preferred_times: List[str] = None) -> List[Dict]:
        """
        Find all available slots across the next 7 days
        
        Args:
            preferred_times: List of preferred time slots (if None, returns ALL available slots)
            
        Returns:
            List of available slots
        """        
        available_slots = []
        dates = self.get_available_dates()
        
        for date in dates:
            self.logger.info(f"Checking availability for {date}")
            availability = self.check_court_availability(date)
            
            if not availability.get('error') and availability.get('status') != 'closed':
                for court, times in availability['courts'].items():
                    for time_slot in times['available_times']:
                        # If preferred_times is specified, filter by it, otherwise return all
                        if preferred_times is None or time_slot in preferred_times:
                            available_slots.append({
                                'date': date,
                                'time': time_slot,
                                'court': court,
                                'status': 'available'
                            })
            
            # Be respectful to the server
            time.sleep(1)
            
        return available_slots
    
    def get_all_slots_summary(self) -> Dict:
        """
        Get a comprehensive summary of all court slots across 7 days
        
        Returns:
            Dict with summary of available, booked, and session slots
        """
        summary = {
            'available_slots': [],
            'booked_slots': [],
            'session_slots': [],
            'closed_days': []
        }
        
        dates = self.get_available_dates()
        
        for date in dates:
            self.logger.info(f"Getting summary for {date}")
            availability = self.check_court_availability(date)
            
            if availability.get('error'):
                continue
                
            if availability.get('status') == 'closed':
                summary['closed_days'].append({
                    'date': date,
                    'message': availability.get('message', 'Closed')
                })
                continue
            
            for court, times in availability['courts'].items():
                for time_slot in times['available_times']:
                    summary['available_slots'].append({
                        'date': date, 'time': time_slot, 'court': court
                    })
                for time_slot in times['booked_times']:
                    summary['booked_slots'].append({
                        'date': date, 'time': time_slot, 'court': court
                    })
                for time_slot in times['session_times']:
                    summary['session_slots'].append({
                        'date': date, 'time': time_slot, 'court': court
                    })
            
            time.sleep(1)  # Be respectful to server
            
        return summary
    
    def book_court(self, date: str, time: str, court: str) -> bool:
        """
        Attempt to book a court (placeholder - requires form analysis)
        
        Note: This is a template. Actual booking requires:
        1. CSRF tokens
        2. Form field analysis
        3. Authentication
        """
        self.logger.warning("Booking functionality not implemented - requires manual form analysis")
        return False
    
    def monitor_availability(self, preferred_times: List[str], check_interval: int = 300):
        """
        Monitor court availability and alert when slots become available
        
        Args:
            preferred_times: List of preferred time slots
            check_interval: Check interval in seconds (default: 5 minutes)
        """
        self.logger.info(f"Starting availability monitor for times: {preferred_times}")
        
        while True:
            try:
                available_slots = self.find_available_slots(preferred_times)
                
                if available_slots:
                    self.logger.info(f"Found {len(available_slots)} available slots:")
                    for slot in available_slots:
                        self.logger.info(f"  {slot['date']} at {slot['time']} - {slot['court']}")
                else:
                    self.logger.info("No available slots found")
                
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                self.logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error during monitoring: {e}")
                time.sleep(60)  # Wait longer on error

def main():
    """Example usage"""
    checker = StJohnsParkChecker()
    
    # Initialize session
    if not checker.initialize_session():
        print("Failed to initialize session")
        return
    
    # Check availability for today
    today = datetime.now().strftime('%Y-%m-%d')
    availability = checker.check_court_availability(today)
    print(json.dumps(availability, indent=2))
    
    # Find ALL available slots (not just evening)
    all_slots = checker.find_available_slots()  # No preferred_times = check all times
    if all_slots:
        print(f"\nFound {len(all_slots)} available slots:")
        for slot in all_slots:
            print(f"  {slot['date']} at {slot['time']} - {slot['court']}")
    else:
        print("\nNo available slots found")
        
    # You can also check specific times if needed:
    # evening_slots = checker.find_available_slots(['6pm', '7pm', '8pm'])
    # morning_slots = checker.find_available_slots(['7am', '8am', '9am'])

if __name__ == "__main__":
    main()