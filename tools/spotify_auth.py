#!/usr/bin/env python3
"""One-time helper: get a Spotify refresh token for the README updater.

1. Create an app at https://developer.spotify.com/dashboard and add
   http://127.0.0.1:8888/callback as a Redirect URI.
2. Run:  SPOTIFY_CLIENT_ID=... SPOTIFY_CLIENT_SECRET=... python3 tools/spotify_auth.py
3. Approve access in the browser. The refresh token is printed here.

The token only grants read access to your top tracks (scope: user-top-read).
"""
import base64
import http.server
import json
import os
import secrets
import urllib.parse
import urllib.request
import webbrowser

REDIRECT_URI = "http://127.0.0.1:8888/callback"
SCOPE = "user-top-read"


def main():
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise SystemExit("Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET first.")

    state = secrets.token_urlsafe(16)
    result = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if query.get("state", [""])[0] == state:
                result["code"] = query.get("code", [None])[0]
                result["error"] = query.get("error", [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Done. You can close this tab and return to the terminal.")

        def log_message(self, *args):
            pass

    url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(
        {"client_id": client_id, "response_type": "code", "redirect_uri": REDIRECT_URI, "scope": SCOPE, "state": state}
    )
    print("Opening the Spotify consent page. If nothing opens, visit:\n" + url)
    webbrowser.open(url)

    with http.server.HTTPServer(("127.0.0.1", 8888), Handler) as server:
        while "code" not in result:
            server.handle_request()
    if not result["code"]:
        raise SystemExit(f"Spotify did not grant access: {result['error']}")

    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    request = urllib.request.Request(
        "https://accounts.spotify.com/api/token",
        data=urllib.parse.urlencode(
            {"grant_type": "authorization_code", "code": result["code"], "redirect_uri": REDIRECT_URI}
        ).encode(),
        headers={"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        token = json.loads(response.read())
    print("\nSPOTIFY_REFRESH_TOKEN:\n" + token["refresh_token"])


if __name__ == "__main__":
    main()
