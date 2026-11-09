"""One-time YouTube OAuth authentication script with exact URL printing and reliable callback.
"""
import os
import sys
import wsgiref.simple_server
from google_auth_oauthlib.flow import (
    InstalledAppFlow,
    _ExclusiveWSGIServer,
    _RedirectWSGIApp,
    _WSGIRequestHandler
)
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.readonly'
]

CLIENT_SECRET_FILE = 'client_secret.json'
TOKEN_FILE = 'youtube_token.json'

def main():
    if not os.path.exists(CLIENT_SECRET_FILE):
        print(f"Error: {CLIENT_SECRET_FILE} not found!", flush=True)
        return

    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    flow.redirect_uri = 'http://localhost:8088/'

    auth_url, state = flow.authorization_url(prompt='consent', access_type='offline')

    print("=" * 80, flush=True)
    print("CLICK THIS URL TO SIGN IN:", flush=True)
    print(auth_url, flush=True)
    print("=" * 80, flush=True)

    wsgi_app = _RedirectWSGIApp("YouTube authentication successful! You can close this window now.")
    local_server = wsgiref.simple_server.make_server(
        'localhost',
        8088,
        wsgi_app,
        server_class=_ExclusiveWSGIServer,
        handler_class=_WSGIRequestHandler
    )

    try:
        print("\nWaiting for authentication in browser...", flush=True)
        local_server.handle_request()
        auth_response = wsgi_app.last_request_uri.replace("http://", "https://")
        flow.fetch_token(authorization_response=auth_response)
        creds = flow.credentials

        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())

        print(f"\nSUCCESS! Token saved to {TOKEN_FILE}", flush=True)

        youtube = build('youtube', 'v3', credentials=creds)
        res = youtube.channels().list(mine=True, part='snippet').execute()
        items = res.get('items', [])
        if items:
            print(f"Verified Channel Name: '{items[0]['snippet']['title']}'", flush=True)
        else:
            print("Connected successfully! (No channel created on this account yet - you can create one anytime).", flush=True)

    finally:
        local_server.server_close()

if __name__ == '__main__':
    main()
