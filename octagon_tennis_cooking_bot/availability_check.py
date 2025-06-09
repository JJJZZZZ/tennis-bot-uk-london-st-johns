import aiohttp
import asyncio
import datetime
import argparse

async def login(email, password):
    LOGIN_URL = "https://rioc.civicpermits.com/Account/Login?ReturnUrl=%2f"
    async with aiohttp.ClientSession() as session:
        payload = {
            'Email': email,
            'Password': password,
            'RememberMe': 'false'
        }
        async with session.post(LOGIN_URL, data=payload) as response:
            text = await response.text()
            if response.status == 200 and "New Permit Request" in text:
                cookies = session.cookie_jar.filter_cookies(LOGIN_URL)
                return {cookie.key: cookie.value for cookie in cookies.values()}
            else:
                raise Exception(f"Login failed with status code {response.status} and response: {text}")

async def check_court_availability(session, api_url, headers, payload):
    async with session.post(api_url, headers=headers, json=payload) as response:
        if response.status == 200:
            return await response.json()
        else:
            return None

async def main(relative_days):
    EMAIL = "jjjzzzzlalala@gmail.com"
    PASSWORD = "Lalala@222"

    AVAILABILITY_API_URL = "https://rioc.civicpermits.com/Permits/ConflictCheck"
    HEADERS = {
        'Content-Type': 'application/json; charset=UTF-8',
        'Accept': '*/*',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    }

    COURT_IDS = {
        '036dfea4-c487-47b0-b7fe-c9cbe52b7c98': 'Octagon Tennis 1',
        '175bdff8-016e-46ab-a9df-829fe40c0754': 'Octagon Tennis 2',
        '9bdef00b-afa0-4b6b-bf9a-75899f7f97c7': 'Octagon Tennis 3',
        'd311851d-ce53-49fc-9662-42adcda26109': 'Octagon Tennis 4',
        '8a5ca8e8-3be0-4145-a4ef-91a69671295b': 'Octagon Tennis 5',
        '77c7f42c-8891-4818-a610-d5c1027c62fe': 'Octagon Tennis 6'
    }

    target_date = (datetime.datetime.now() + datetime.timedelta(days=relative_days)).strftime('%Y-%m-%d')

    tasks = []

    cookies = await login(EMAIL, PASSWORD)
    cookie_header = "; ".join([f"{key}={value}" for key, value in cookies.items()])

    headers = HEADERS.copy()
    headers['Cookie'] = cookie_header

    async with aiohttp.ClientSession() as session:
        for hour in range(8, 22):  # From 8 AM to 10 PM
            for court_id, court_name in COURT_IDS.items():
                payload = {
                    "facilityNames": ["Tennis Courts"],
                    "facilityIds": [court_id],
                    "dates": [{"start": f"{target_date}T{hour:02d}:00:00", "stop": f"{target_date}T{hour+1:02d}:00:00"}]
                }
                tasks.append(check_court_availability(session, AVAILABILITY_API_URL, headers, payload))

        responses = await asyncio.gather(*tasks)

    available_courts_by_time = {f"{hour:02d}:00": [] for hour in range(8, 22)}

    for hour in range(8, 22):
        for response, (court_id, court_name) in zip(responses[(hour-8)*len(COURT_IDS):(hour-7)*len(COURT_IDS)], COURT_IDS.items()):
            if response == []:
                available_courts_by_time[f"{hour:02d}:00"].append(court_name)

    print(f"Available courts on {target_date}:")
    for time, courts in available_courts_by_time.items():
        if courts:
            print(f"Time: {time} - Courts: {', '.join(courts)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check court availability for a given number of relative days from today.")
    parser.add_argument("--days", type=int, required=True, help="Number of days from today to check availability for")
    args = parser.parse_args()
    
    asyncio.run(main(args.days))