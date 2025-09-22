import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# --- Step 1: Authentication ---
# This function handles the OAuth 2.0 flow.
def get_credentials():
    # Define the 'scopes' - what permissions we're asking for.
    # This scope allows managing business profiles.
    scopes = ['https://www.googleapis.com/auth/business.manage']
    
    # Path to your downloaded client_secret.json file.
    client_secrets_file = 'client_secret.json'

    # Run the authorization flow. The first time you run this, a browser
    # window will open asking you to log in with your Google account and
    # grant permission.
    flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
    credentials = flow.run_local_server(port=0)
    
    return credentials

# --- Main part of the script ---
# --- Main part of the script ---
if __name__ == '__main__':
    # Get the authenticated credentials.
    creds = get_credentials()

    # Build the service objects for the APIs you want to use.
    account_api = build('mybusinessaccountmanagement', 'v1', credentials=creds)
    info_api = build('mybusinessbusinessinformation', 'v1', credentials=creds)
    
    # --- THIS IS THE CORRECTED LINE ---
    performance_api = build('businessprofileperformance', 'v1', credentials=creds)

    try:
        # --- Step 2: Use the Account Management API ---
        print("--- Fetching Accounts ---")
        accounts_result = account_api.accounts().list().execute()
        
        if not accounts_result.get('accounts'):
            print("No business accounts found for this user.")
        else:
            first_account = accounts_result['accounts'][0]
            account_name = first_account['name']
            print(f"Found Account: {account_name}\n")

            # --- Step 3: Use the Business Information API ---
            print("--- Fetching Business Locations ---")
            locations_result = info_api.accounts().locations().list(parent=account_name).execute()
            
            if not locations_result.get('locations'):
                print("No locations found in this account.")
            else:
                first_location = locations_result['locations'][0]
                location_name = first_location['name']
                business_title = first_location.get('title', 'N/A')
                phone_number = first_location.get('phoneNumbers', {}).get('primaryPhone', 'N/A')

                print(f"Found Location ID: {location_name}")
                print(f"Business Title: {business_title}")
                print(f"Phone Number: {phone_number}\n")

                # --- Step 4: Use the Business Profile Performance API ---
                print("--- Fetching Performance Data ---")
                
                # NOTE: I've updated the date range to the last 30 days of August 2025
                # to ensure it's a valid period.
                report = performance_api.locations().getDailyMetricsTimeSeries(
                    name=location_name,
                    dailyMetric='VIEWS_SEARCH',
                    dailyRange_startDate_year=2025,
                    dailyRange_startDate_month=8,
                    dailyRange_startDate_day=1,
                    dailyRange_endDate_year=2025,
                    dailyRange_endDate_month=8,
                    dailyRange_endDate_day=30
                ).execute()
                
                time_series_data = report.get('timeSeries', [])
                if not time_series_data:
                    print("No performance data found for the specified period.")
                else:
                    total_views = 0
                    for series in time_series_data:
                        for point in series.get('datedValues', []):
                            total_views += int(point.get('value', 0))
                    print(f"Total views on Google Search in the specified period: {total_views}")

    except Exception as e:
        print(f"An error occurred: {e}")