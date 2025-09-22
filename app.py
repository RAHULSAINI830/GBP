import os
import json
from flask import Flask, redirect, request, session, url_for, render_template, jsonify
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your_default_secret_key") # Use environment variable for secret key

# --- Configuration ---
SCOPES = ['https://www.googleapis.com/auth/business.manage']

# --- THIS IS THE CRITICAL CHANGE ---
# Dynamically set the REDIRECT_URI based on the environment
if os.getenv('VERCEL_URL'):
    # This is the production environment on Vercel
    REDIRECT_URI = f"https://{os.getenv('VERCEL_URL')}/oauth2callback"
    # Allow HTTPS for OAuthlib in production
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '0'
else:
    # This is the local development environment
    REDIRECT_URI = 'http://127.0.0.1:5000/oauth2callback'
    # Allow HTTP for OAuthlib in local development
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


def get_flow():
    """Initializes the OAuth 2.0 flow, loading secrets from environment or file."""
    client_config_json_str = os.getenv('GOOGLE_CLIENT_SECRET_JSON')

    if client_config_json_str:
        # If the environment variable is found (on Vercel), load from it
        client_config = json.loads(client_config_json_str)
        return Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
    else:
        # If not found (running locally), load from the client_secret.json file
        return Flow.from_client_secrets_file(
            'client_secret.json',
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )

# --- The rest of your app.py remains the same ---

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
    # Use the full request URL to handle the callback correctly
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
    if 'credentials' not in session:
        return jsonify({'error': 'User not authenticated'}), 401

    creds = Credentials(**session['credentials'])

    try:
        account_api = build('mybusinessaccountmanagement', 'v_1', credentials=creds)
        info_api = build('mybusinessbusinessinformation', 'v_1', credentials=creds)

        accounts_result = account_api.accounts().list().execute()
        if not accounts_result.get('accounts'):
            return jsonify({'error': 'No business accounts found.'}), 404

        first_account = accounts_result['accounts'][0]
        account_name = first_account['name']

        locations_result = info_api.accounts().locations().list(parent=account_name).execute()
        locations_data = locations_result.get('locations', [])

        return jsonify({
            'account': first_account,
            'locations': locations_data
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
