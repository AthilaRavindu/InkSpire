"""
One-time Pinterest OAuth helper — run this on your own machine, not in CI.

It opens Pinterest in your browser, catches the redirect, and prints the
refresh token to store as a GitHub secret.

Usage:
    pip install requests
    set PINTEREST_APP_ID=your_app_id
    set PINTEREST_APP_SECRET=your_app_secret
    python .github/scripts/pinterest_auth.py

Register this exact redirect URI in your Pinterest app settings first:
    http://localhost:8085/callback

Screen-record this run — Pinterest requires a video of the OAuth flow when
you apply for Standard access.
"""

import os
import sys
import base64
import webbrowser
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

REDIRECT_URI = "http://localhost:8085/callback"
SCOPES = "boards:read,boards:write,pins:read,pins:write"

APP_ID = os.environ.get("PINTEREST_APP_ID")
APP_SECRET = os.environ.get("PINTEREST_APP_SECRET")

if not APP_ID or not APP_SECRET:
    print("Set PINTEREST_APP_ID and PINTEREST_APP_SECRET first.")
    print("Find both at https://developers.pinterest.com/apps/")
    sys.exit(1)

auth_code = {}


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

        if "code" in params:
            auth_code["code"] = params["code"][0]
            body = "<h2>Authorized.</h2><p>You can close this tab and return to the terminal.</p>"
        else:
            body = f"<h2>Authorization failed.</h2><pre>{params}</pre>"

        self.wfile.write(body.encode("utf-8"))

    def log_message(self, *args):
        pass  # keep the terminal readable


def main():
    auth_url = (
        "https://www.pinterest.com/oauth/?"
        + urllib.parse.urlencode({
            "client_id": APP_ID,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": SCOPES,
        })
    )

    print("Opening Pinterest authorization page...")
    print(f"If the browser does not open, paste this URL manually:\n{auth_url}\n")
    webbrowser.open(auth_url)

    server = HTTPServer(("localhost", 8085), CallbackHandler)
    print("Waiting for authorization...")
    while "code" not in auth_code:
        server.handle_request()

    print("Authorization code received. Exchanging for tokens...")

    basic = base64.b64encode(f"{APP_ID}:{APP_SECRET}".encode()).decode()
    response = requests.post(
        "https://api.pinterest.com/v5/oauth/token",
        headers={
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "authorization_code",
            "code": auth_code["code"],
            "redirect_uri": REDIRECT_URI,
        },
        timeout=30,
    )

    if response.status_code != 200:
        print(f"Token exchange failed ({response.status_code}):")
        print(response.text)
        sys.exit(1)

    tokens = response.json()
    refresh_token = tokens.get("refresh_token")

    print("\n" + "=" * 60)
    print("SUCCESS — add this to GitHub as a secret named:")
    print("PINTEREST_REFRESH_TOKEN")
    print("=" * 60)
    print(refresh_token)
    print("=" * 60)
    print("\nKeep this private. It grants posting access to your account.")


if __name__ == "__main__":
    main()
