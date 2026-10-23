"""
Inkspire Pinterest Pin Pack Generator
Uses Google Gemini free tier.
Generates 7 ready-to-post pins — paste into Pinterest's free built-in scheduler.
"""

import os
import time
import datetime
from google import genai
from google.genai import errors as genai_errors

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Google rotates model availability often. Lite variants carry far less traffic,
# so they are tried first — a 404 means retired, a 503 means overloaded.
MODEL_CHAIN = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.8-flash",
]


def generate_with_retry(prompt, retries=3, delay=20):
    last_error = None
    for model_name in MODEL_CHAIN:
        for attempt in range(retries):
            try:
                response = client.models.generate_content(model=model_name, contents=prompt)
                return response.text
            except genai_errors.ClientError as e:
                print(f"{model_name} unavailable ({e.code}) — trying next model")
                last_error = e
                break
            except genai_errors.ServerError as e:
                last_error = e
                if attempt < retries - 1:
                    print(f"{model_name} busy, retry {attempt + 1}/{retries} in {delay}s...")
                    time.sleep(delay)
                else:
                    print(f"{model_name} still busy — trying next model")

    print("\nAll models failed. Models visible to this API key:")
    for m in client.models.list():
        print(f"  {m.name}")
    raise last_error

SITE_URL = "https://athilaravindu.github.io/InkSpire"

# Each theme is paired with the article it actually sends readers to, so the
# pin copy and the destination page always match.
WEEKLY_THEMES = [
    ("Monday Motivation", "tattoo inspiration and motivation for people thinking about getting inked",
     "tattoo-trends-2025.html"),
    ("Style Tuesday", "the fine line tattoo style — delicate, minimalist, detailed work",
     "fine-line-guide.html"),
    ("Wednesday Wisdom", "tattoo aftercare tips and how to keep tattoos looking fresh long-term",
     "aftercare-guide.html"),
    ("Trend Thursday", "trending tattoo designs in the USA right now",
     "tattoo-trends-2025.html"),
    ("Artist Friday", "how to find, vet, and book the right tattoo artist",
     "find-tattoo-artist.html"),
    ("Weekend Inspo", "tattoo placement ideas — where on the body different styles work best",
     "fine-line-guide.html"),
    ("Sunday Spotlight", "what to ask an artist before booking, and how to prepare for a session",
     "find-tattoo-artist.html"),
]


def generate_pin_pack(week_start: datetime.date) -> str:
    output = f"# Inkspire Pinterest Pin Pack — Week of {week_start.isoformat()}\n\n"
    output += "_Paste each pin into: pinterest.com/content/scheduled (free scheduler)_\n\n---\n\n"

    for i, (day_name, theme, article_page) in enumerate(WEEKLY_THEMES):
        pin_date = week_start + datetime.timedelta(days=i)
        article_link = f"{SITE_URL}/{article_page}"

        prompt = f"""You are a Pinterest expert writing for Inkspire, a tattoo inspiration site targeting USA tattoo fans aged 18-35.

Write ONE Pinterest pin for: {day_name} ({pin_date.strftime('%B %d, %Y')})
Theme: {theme}
Link: {article_link}

Rules:
- Title: max 100 characters, strong curiosity hook
- Description: 150-250 characters, ends with 4-5 hashtags mixing popular (#tattoo #tattooinspo) and niche ones
- The title and description must promise ONLY what the theme above covers, since that is
  what the linked page delivers. Do not tease a different topic in the call to action.
- Suggest one board: Tattoo Ideas | Tattoo Aftercare | Tattoo Styles | Tattoo Inspiration | Fine Line Tattoos
- Image: one sentence describing what to search on Pexels or Unsplash

Reply in EXACTLY this format, no extra text:
TITLE: [title]
DESCRIPTION: [description + hashtags]
BOARD: [board name]
IMAGE: [image search suggestion]"""

        pin_text = generate_with_retry(prompt)
        output += f"## {day_name} — {pin_date.strftime('%A %B %d')}\n\n"
        output += pin_text.strip() + "\n"
        output += f"URL: {article_link}\n\n---\n\n"
        time.sleep(5)  # avoid hitting rate limits between pins

    return output


def save_pin_pack(content: str, week_start: datetime.date):
    os.makedirs("_pinterest_pins", exist_ok=True)
    path = f"_pinterest_pins/{week_start.isoformat()}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Pin pack saved: {path}")
    print("Open it and paste into: https://pinterest.com/content/scheduled")


if __name__ == "__main__":
    today = datetime.date.today()
    days_ahead = (7 - today.weekday()) % 7
    week_start = today + datetime.timedelta(days=days_ahead if days_ahead else 7)

    print(f"Generating Pinterest pin pack for week of {week_start}...")
    content = generate_pin_pack(week_start)
    save_pin_pack(content, week_start)
    print("Done.")
