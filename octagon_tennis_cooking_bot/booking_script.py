import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import argparse
import logging

logging.basicConfig(level=logging.INFO)

def main(selected_time, email, password, relative_days):
    # Constants
    LOGIN_URL = "https://rioc.civicpermits.com/Account/Login?ReturnUrl=%2f"

    SITE_TO_CHECKBOX_MAP = {
        '3c9230f0-9e2c-4ff0-8ad7-5300eb475af5': '036dfea4-c487-47b0-b7fe-c9cbe52b7c98',  # Octagon Tennis 1
        'f96d68ab-adea-42cb-8b42-c45a89e7ae2b': '175bdff8-016e-46ab-a9df-829fe40c0754',  # Octagon Tennis 2
        '5633e568-7db6-4e84-a02b-3ac827406bfc': '9bdef00b-afa0-4b6b-bf9a-75899f7f97c7',  # Octagon Tennis 3
        '3e83f44d-ed76-4a95-a73e-e9c5dcfa6e55': 'd311851d-ce53-49fc-9662-42adcda26109',  # Octagon Tennis 4
        '2158c5f2-8734-4755-b2ef-2627d4a5f0b1': '8a5ca8e8-3be0-4145-a4ef-91a69671295b',  # Octagon Tennis 5
        'f3794e38-71ac-4440-9f3b-1adce02df1d7': '77c7f42c-8891-4818-a610-d5c1027c62fe'   # Octagon Tennis 6
    }

    COURT_NAME_MAP = {
        '3c9230f0-9e2c-4ff0-8ad7-5300eb475af5': 'Octagon Tennis 1',
        'f96d68ab-adea-42cb-8b42-c45a89e7ae2b': 'Octagon Tennis 2',
        '5633e568-7db6-4e84-a02b-3ac827406bfc': 'Octagon Tennis 3',
        '3e83f44d-ed76-4a95-a73e-e9c5dcfa6e55': 'Octagon Tennis 4',
        '2158c5f2-8734-4755-b2ef-2627d4a5f0b1': 'Octagon Tennis 5',
        'f3794e38-71ac-4440-9f3b-1adce02df1d7': 'Octagon Tennis 6'
    }

    def get_court_order(selected_time):
        if int(selected_time) < 12:  # Morning session before 12 PM
            return [
                '3c9230f0-9e2c-4ff0-8ad7-5300eb475af5',  # Octagon Tennis 1
                '3e83f44d-ed76-4a95-a73e-e9c5dcfa6e55',  # Octagon Tennis 4
                '5633e568-7db6-4e84-a02b-3ac827406bfc',  # Octagon Tennis 3
                'f3794e38-71ac-4440-9f3b-1adce02df1d7',  # Octagon Tennis 6
                'f96d68ab-adea-42cb-8b42-c45a89e7ae2b',  # Octagon Tennis 2
                '2158c5f2-8734-4755-b2ef-2627d4a5f0b1'   # Octagon Tennis 5
            ]
        else:  # Afternoon or evening session
            return [
                'f3794e38-71ac-4440-9f3b-1adce02df1d7',  # Octagon Tennis 6
                '5633e568-7db6-4e84-a02b-3ac827406bfc',  # Octagon Tennis 3
                '3e83f44d-ed76-4a95-a73e-e9c5dcfa6e55',  # Octagon Tennis 4
                '3c9230f0-9e2c-4ff0-8ad7-5300eb475af5',  # Octagon Tennis 1
                '2158c5f2-8734-4755-b2ef-2627d4a5f0b1',  # Octagon Tennis 5
                'f96d68ab-adea-42cb-8b42-c45a89e7ae2b'   # Octagon Tennis 2
            ]

    # Determine court order based on the selected time
    COURT_IDS = get_court_order(selected_time)

    # Initialize driver to None
    driver = None
    final_result = ""

    try:
        # Suppress logging output
        logging.getLogger().setLevel(logging.CRITICAL)
        
        # Initialize Chrome options
        options = webdriver.ChromeOptions()
        options.add_experimental_option("detach", True)
        # options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        
        # Use WebDriverManager to handle Chromedriver updates automatically
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        # Restore logging level
        logging.getLogger().setLevel(logging.INFO)
        
        try:
            # Functions
            def login(driver, email, password):
                driver.get(LOGIN_URL)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'loginEmail'))).send_keys(email)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'loginPassword'))).send_keys(password)
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[@tabindex="3"]'))).click()

            def navigate_to_new_permit_request(driver):
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, "New Permit Request"))).click()

            def select_site_and_checkbox(driver, site_id):
                # Select the site by its ID
                site_select = Select(WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, 'site'))))
                site_select.select_by_value(site_id)

                # Get the initial text of the correct element
                initial_text = driver.find_element(By.ID, "siteDescription").text
                # print(f"Initial text: {initial_text}")

                # Wait for the text of the correct element to change from its initial value
                WebDriverWait(driver, 10).until(lambda driver: driver.find_element(By.ID, "siteDescription").text != initial_text)

                # Get the new text of the correct element
                new_text = driver.find_element(By.ID, "siteDescription").text
                # print(f"New text: {new_text}")

                # Click on the add facility set button
                add_facility_set_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "addFacilitySet")))
                add_facility_set_button.click()

                # Wait for the checkbox to be clickable and click on it
                checkbox_id = SITE_TO_CHECKBOX_MAP[site_id]
                checkbox = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, checkbox_id)))
                checkbox.click()

            def select_date_and_time(driver, selected_time, relative_days):
                target_date = datetime.datetime.now() + datetime.timedelta(days=relative_days)
                target_day = str(target_date.day)
                target_month = target_date.strftime('%B')
                target_year = target_date.year

                driver.find_element(By.ID, 'event0').click()
                WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "ui-datepicker")))

                while True:
                    headers = driver.find_elements(By.CLASS_NAME, "ui-datepicker-title")
                    found = False

                    for header in headers:
                        month_text, year = header.text.split()
                        year = int(year)

                        if year == target_year and month_text == target_month:
                            driver.find_element(By.XPATH, f'//a[text()="{target_day}"]').click()
                            found = True
                            break

                    if found:
                        break
                    else:
                        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "ui-datepicker-next"))).click()
                        WebDriverWait(driver, 10).until(EC.staleness_of(headers[0]))

                Select(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "startHour")))).select_by_value(selected_time)
                Select(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "endHour")))).select_by_value(str((int(selected_time) + 1) % 24))

            def book_court(driver):
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[text()="Add & Confirm"]'))).click()

            def check_error_message(driver):
                try:
                    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//label[@class='error' and contains(text(), 'The selected facilities are not available for the above date and time.')]")))
                    return True
                except:
                    return False

            def try_booking_other_courts(driver):
                for court_id in COURT_IDS:
                    try:
                        court_name = COURT_NAME_MAP[court_id]
                        Select(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'site')))).select_by_value(court_id)
                        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, SITE_TO_CHECKBOX_MAP[court_id]))).click()
                        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//button[text()="Add & Confirm"]'))).click()

                        if WebDriverWait(driver, 2, 0.1).until(EC.invisibility_of_element_located((By.XPATH, '//button[text()="Add & Confirm"]'))):
                            return f"Booking successful for {court_name} under account {email} for time {selected_time} on day {relative_days}."
                    except:
                        continue
                return f"Booking failed under account {email} for time {selected_time} on day {relative_days}."

            def fill_additional_details(driver):
                input_data = {
                    '11e79e5d3daf4712b9e6418d2691b976': "Tennis",
                    'af8966101be44676b4ee564b052e1e87': '2',
                    'f28f0dbea8b5438495778b0bb0ddcd93': 'No',
                    'd46cb434558845fb9e0318ab6832e427': 'No',
                    '1221940f5cca4abdb5288cfcbe284820': 'No',
                    '0ce54956c4b14746ae5d364507da1e85': 'No',
                    '6b1dda4172f840c7879662bcab1819db': 'No',
                    'a31f4297075e4dab8c0ef154f2b9b1c1': '0',
                    'activity': "Tennis"
                }

                for input_id, value in input_data.items():
                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, input_id))).send_keys(value)

                select_data = {
                    '3754dcef7216446b9cc4bf1cd0f12a2e': 'No',
                    '06b3f73192a84fd6b88758e56a64c3ad': 'No'
                }

                for select_id, value in select_data.items():
                    Select(WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, select_id)))).select_by_visible_text(value)

                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'acceptTerms'))).click()

            def submit_form(driver):
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[text()="Submit"]'))).click()

            def wait_until_8am():
                now = datetime.datetime.now()
                target_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
                if now < target_time:
                    wait_seconds = (target_time - now).total_seconds()
                    time.sleep(wait_seconds)
                else:
                    pass

            # Start of booking process
            login(driver, email, password)
            navigate_to_new_permit_request(driver)
            wait_until_8am()  # Wait until 8 AM before proceeding
            select_site_and_checkbox(driver, COURT_IDS[0])
            select_date_and_time(driver, selected_time, relative_days)
            book_court(driver)

            if check_error_message(driver):
                final_result = try_booking_other_courts(driver)
            else:
                final_result = f"Booking successful for {COURT_NAME_MAP[COURT_IDS[0]]} under account {email} for time {selected_time} on day {relative_days}."

            fill_additional_details(driver)
            submit_form(driver)

        except Exception as e:
            final_result = f"An error occurred during execution: {str(e)}"
    except Exception as e:
        final_result = f"An error occurred during driver initialization: {str(e)}"
    finally:
        logging.info(final_result)
        if driver is not None:
            driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Automated Court Booking')
    parser.add_argument('--time', type=str, required=True, help='Selected time for booking')
    parser.add_argument('--email', type=str, required=True, help='Email for login')
    parser.add_argument('--password', type=str, required=True, help='Password for login')
    parser.add_argument('--days', type=int, required=True, help='Relative days for booking (0 for today, 1 for tomorrow, etc.)')
    args = parser.parse_args()
    main(args.time, args.email, args.password, args.days)