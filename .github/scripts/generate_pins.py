"""
Inkspire Pinterest Pin Pack Generator
Uses Google Gemini 2.5 Flash — permanently free tier.
Generates 7 ready-to-post pins — paste into Pinterest's free built-in scheduler.
"""

import os
import datetime
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

SITE_URL = "https://athilaravindu.github.io/InkSpire"

WEEKLY_THEMES = [
    ("Monday Motivation", "tattoo inspiration and motivation for people thinking about getting inked"),
    ("Style Tuesday", "a specific tattoo style — fine line, blackwork, Japanese, geometric, or watercolour"),
    ("Wednesday Wisdom", "tattoo aftercare tips and how to keep tattoos looking fresh long-term"),
    ("Trend Thursday", "trending tattoo designs in the USA right now"),
    ("Artist Friday", "how to find, vet, and book the right tattoo artist"),
    ("Weekend Inspo", "tattoo placement ideas and body art inspiration"),
    ("Sunday Spotlight", "an educational deep-dive into one tattoo topic"),
]

ARTICLE_LINKS = [
    f"{SITE_URL}/aftercare-guide.html",
    f"{SITE_URL}/tattoo-trends-2025.html",
    f"{SITE_URL}/find-tattoo-artist.html",
    f"{SITE_URL}/fine-line-guide.html",
]


def generate_pin_pack(week_start: datetime.date) -> str:
    output = f"# Inkspire Pinterest Pin Pack — Week of {week_start.isoformat()}\n\n"
    output += "_Paste each pin into: pinterest.com/content/scheduled (free scheduler)_\n\n---\n\n"

    for i, (day_name, theme) in enumerate(WEEKLY_THEMES):
        pin_date = week_start + datetime.timedelta(days=i)
        article_link = ARTICLE_LINKS[i % len(ARTICLE_LINKS)]

        prompt = f"""You are a Pinterest expert writing for Inkspire, a tattoo inspiration site targeting USA tattoo fans aged 18-35.

Write ONE Pinterest pin for: {day_name} ({pin_date.strftime('%B %d, %Y')})
Theme: {theme}
Link: {article_link}

Rules:
- Title: max 100 characters, strong curiosity hook
- Description: 150-250 characters, ends with 4-5 hashtags mixing popular (#tattoo #tattooinspo) and niche ones
- Suggest one board: Tattoo Ideas | Tattoo Aftercare | Tattoo Styles | Tattoo Inspiration | Fine Line Tattoos
- Image: one sentence describing what to search on Pexels or Unsplash

Reply in EXACTLY this format, no extra text:
TITLE: [title]
DESCRIPTION: [description + hashtags]
BOARD: [board name]
IMAGE: [image search suggestion]"""

        response = model.generate_content(prompt)
        output += f"## {day_name} — {pin_date.strftime('%A %B %d')}\n\n"
        output += response.text.strip() + "\n"
        output += f"URL: {article_link}\n\n---\n\n"

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
