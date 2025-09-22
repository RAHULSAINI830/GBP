import os
from flask import Flask, redirect, request, session, url_for, render_template, jsonify
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)
# Replace this with a real secret key in a production environment
app.secret_key = 'your_super_secret_key'
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # For local testing with HTTP

# --- Configuration ---
CLIENT_SECRETS_FILE = 'client_secret.json'
SCOPES = ['https://www.googleapis.com/auth/business.manage']
REDIRECT_URI = 'http://127.0.0.1:5000/oauth2callback'

def get_flow():
    """Initializes the OAuth 2.0 flow."""
    return Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

@app.route('/')
def index():
    """Renders the main page."""
    return render_template('index.html')

@app.route('/login')
def login():
    """Redirects the user to Google's OAuth 2.0 server."""
    flow = get_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    """Handles the callback from Google after user authorization."""
    state = session.get('state')
    flow = get_flow()
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    # Store credentials in the session.
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    """Clears the session to log the user out."""
    session.clear()
    return redirect(url_for('index'))

@app.route('/api/get-business-data')
def get_business_data():
    """API endpoint to fetch business data for the frontend."""
    # Check if user is logged in by looking for credentials in the session
    if 'credentials' not in session:
        return jsonify({'error': 'User not authenticated'}), 401

    # Recreate credentials object from the session data
    creds = Credentials(**session['credentials'])

    try:
        # Build the API services
        account_api = build('mybusinessaccountmanagement', 'v1', credentials=creds)
        info_api = build('mybusinessbusinessinformation', 'v1', credentials=creds)

        # Get accounts
        accounts_result = account_api.accounts().list().execute()
        if not accounts_result.get('accounts'):
            return jsonify({'error': 'No business accounts found.'}), 404

        first_account = accounts_result['accounts'][0]
        account_name = first_account['name']

        # Get locations from the first account
        locations_result = info_api.accounts().locations().list(parent=account_name).execute()
        
        # Prepare the data for the frontend
        locations_data = locations_result.get('locations', [])

        return jsonify({
            'account': first_account,
            'locations': locations_data
        })

    except Exception as e:
        # If something goes wrong, return an error
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)