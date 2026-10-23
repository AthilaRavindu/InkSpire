"""
Posts today's pin to Pinterest from the current week's generated pack.

Runs daily. One pin per day rather than seven at once, because burst-posting
reads as spam to Pinterest's ranking and suppresses distribution.

Exits quietly (status 0) when credentials are absent, so the workflow keeps
succeeding while Standard API access is still pending approval.
"""

import os
import re
import sys
import base64
import datetime
import requests

PINTEREST_API = "https://api.pinterest.com/v5"
PEXELS_SEARCH = "https://api.pexels.com/v1/search"

APP_ID = os.environ.get("PINTEREST_APP_ID")
APP_SECRET = os.environ.get("PINTEREST_APP_SECRET")
REFRESH_TOKEN = os.environ.get("PINTEREST_REFRESH_TOKEN")
PEXELS_KEY = os.environ.get("PEXELS_API_KEY")


def require_config():
    missing = [name for name, value in [
        ("PINTEREST_APP_ID", APP_ID),
        ("PINTEREST_APP_SECRET", APP_SECRET),
        ("PINTEREST_REFRESH_TOKEN", REFRESH_TOKEN),
        ("PEXELS_API_KEY", PEXELS_KEY),
    ] if not value]

    if missing:
        print("Pinterest auto-posting is not configured yet.")
        print("Missing secrets: " + ", ".join(missing))
        print("The weekly pin pack is still generated for manual posting.")
        sys.exit(0)


def get_access_token():
    """Pinterest access tokens are short-lived; exchange the refresh token each run."""
    auth = base64.b64encode(f"{APP_ID}:{APP_SECRET}".encode()).decode()
    response = requests.post(
        f"{PINTEREST_API}/oauth/token",
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "refresh_token", "refresh_token": REFRESH_TOKEN},
        timeout=30,
    )
    if response.status_code != 200:
        print(f"Token refresh failed ({response.status_code}): {response.text}")
        sys.exit(1)
    return response.json()["access_token"]


def parse_pack(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()

    pins = []
    for block in text.split("---"):
        fields = {}
        for key in ("TITLE", "DESCRIPTION", "BOARD", "IMAGE_QUERY", "IMAGE", "URL"):
            match = re.search(rf"^{key}:\s*(.+)$", block, re.MULTILINE)
            if match:
                fields[key] = match.group(1).strip()
        if "TITLE" in fields and "URL" in fields:
            pins.append(fields)
    return pins


def find_image(query):
    """Pinterest favours tall images, so portrait orientation is requested."""
    response = requests.get(
        PEXELS_SEARCH,
        headers={"Authorization": PEXELS_KEY},
        params={"query": query, "per_page": 5, "orientation": "portrait"},
        timeout=30,
    )
    if response.status_code != 200:
        print(f"Pexels search failed ({response.status_code}): {response.text}")
        return None

    photos = response.json().get("photos", [])
    if not photos:
        print(f"No Pexels results for '{query}', retrying with a broader query")
        return None
    return photos[0]["src"]["large2x"]


def resolve_board(token, name):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{PINTEREST_API}/boards", headers=headers,
        params={"page_size": 100}, timeout=30,
    )
    if response.status_code != 200:
        print(f"Could not list boards ({response.status_code}): {response.text}")
        sys.exit(1)

    for board in response.json().get("items", []):
        if board["name"].strip().lower() == name.strip().lower():
            return board["id"]

    print(f"Board '{name}' not found — creating it")
    created = requests.post(
        f"{PINTEREST_API}/boards", headers=headers,
        json={"name": name, "privacy": "PUBLIC"}, timeout=30,
    )
    if created.status_code not in (200, 201):
        print(f"Could not create board ({created.status_code}): {created.text}")
        sys.exit(1)
    return created.json()["id"]


def create_pin(token, board_id, pin, image_url):
    body = {
        "board_id": board_id,
        "title": pin["TITLE"][:100],
        "description": pin.get("DESCRIPTION", "")[:800],
        "link": pin["URL"],
        "media_source": {"source_type": "image_url", "url": image_url},
    }
    response = requests.post(
        f"{PINTEREST_API}/pins",
        headers={"Authorization": f"Bearer {token}"},
        json=body, timeout=60,
    )
    if response.status_code not in (200, 201):
        print(f"Pin creation failed ({response.status_code}): {response.text}")
        sys.exit(1)
    return response.json()


if __name__ == "__main__":
    require_config()

    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    pack_path = f"_pinterest_pins/{monday.isoformat()}.md"

    if not os.path.exists(pack_path):
        print(f"No pin pack for this week ({pack_path}). Nothing to post.")
        sys.exit(0)

    pins = parse_pack(pack_path)
    index = today.weekday()
    if index >= len(pins):
        print(f"Pack has {len(pins)} pins; no entry for day {index}. Nothing to post.")
        sys.exit(0)

    pin = pins[index]
    print(f"Posting: {pin['TITLE']}")

    query = pin.get("IMAGE_QUERY") or "tattoo art"
    image_url = find_image(query) or find_image("tattoo")
    if not image_url:
        print("Could not source an image. Aborting without posting.")
        sys.exit(1)

    token = get_access_token()
    board_id = resolve_board(token, pin.get("BOARD", "Tattoo Ideas"))
    result = create_pin(token, board_id, pin, image_url)

    print(f"Posted pin {result.get('id')} to board {pin.get('BOARD')}")
