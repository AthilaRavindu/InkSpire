"""
Inkspire Pinterest Pin Pack Generator
Every Monday, generates 7 ready-to-post Pinterest pins (one per day of the week).
Output: _pinterest_pins/YYYY-MM-DD.md — a Markdown file you open and copy-paste from.
No Pinterest API needed — you paste these into Pinterest's own free scheduler.
"""

import anthropic
import datetime
import os

client = anthropic.Anthropic()

SITE_URL = "https://athilaravindu.github.io/InkSpire"

WEEKLY_THEMES = [
    ("Monday Motivation", "tattoo inspiration and motivation for people thinking about getting their first tattoo"),
    ("Style Tuesday", "a specific tattoo style (fine line, blackwork, Japanese, geometric, watercolour, etc.)"),
    ("Wednesday Wisdom", "tattoo aftercare tips and how to keep tattoos looking fresh"),
    ("Trend Thursday", "trending tattoo designs for 2025, popular in the USA right now"),
    ("Artist Friday", "how to find, vet, and book the right tattoo artist"),
    ("Weekend Inspo", "tattoo placement ideas and body art inspiration for the weekend"),
    ("Sunday Spotlight", "a featured deep-dive into one tattoo topic — educational and shareable"),
]

ARTICLE_LINKS = [
    f"{SITE_URL}/aftercare-guide.html",
    f"{SITE_URL}/tattoo-trends-2025.html",
    f"{SITE_URL}/find-tattoo-artist.html",
    f"{SITE_URL}/fine-line-guide.html",
]

SYSTEM_PROMPT = """You are a Pinterest content expert specialising in tattoo content for a USA audience.
Write compelling Pinterest pin copy that drives saves and clicks.
Pinterest pins that perform best:
- Lead with a benefit or curiosity hook
- Include 3-5 relevant hashtags targeting US tattoo community
- Have a clear call to action linking back to the website
- Use ALL CAPS for emphasis sparingly
- Feel personal and enthusiastic, not corporate
- 150-300 characters for description (Pinterest optimal length)"""


def generate_pin_pack(week_start: datetime.date) -> str:
    pins_text = f"# Inkspire Pinterest Pin Pack — Week of {week_start.isoformat()}\n\n"
    pins_text += "_Copy these into Pinterest's scheduler: pinterest.com/content/scheduled_\n\n"
    pins_text += "---\n\n"

    for i, (day_name, theme) in enumerate(WEEKLY_THEMES):
        pin_date = week_start + datetime.timedelta(days=i)
        article_link = ARTICLE_LINKS[i % len(ARTICLE_LINKS)]

        prompt = f"""Write ONE Pinterest pin for Inkspire tattoo website.

Day: {day_name} ({pin_date.strftime('%B %d, %Y')})
Theme: {theme}
Link this pin to: {article_link}

Format your response EXACTLY like this (no extra text):
TITLE: [pin title, max 100 chars]
DESCRIPTION: [engaging description 150-250 chars with 4-5 hashtags]
BOARD: [suggest which Pinterest board name to post to]
IMAGE IDEA: [one sentence describing the ideal image for this pin — what to search on Pexels/Unsplash]"""

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )

        pin_content = message.content[0].text
        pins_text += f"## {day_name} — {pin_date.strftime('%A, %B %d')}\n\n"
        pins_text += f"{pin_content}\n"
        pins_text += f"URL: {article_link}\n"
        pins_text += "\n---\n\n"

    return pins_text


def save_pin_pack(content: str, week_start: datetime.date):
    output_dir = "_pinterest_pins"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{output_dir}/{week_start.isoformat()}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Pinterest pin pack saved: {filename}")
    print("Open this file and paste each pin into: https://pinterest.com/content/scheduled")


if __name__ == "__main__":
    today = datetime.date.today()
    # Start from next Monday
    days_until_monday = (7 - today.weekday()) % 7
    week_start = today + datetime.timedelta(days=days_until_monday if days_until_monday else 7)

    print(f"Inkspire: generating Pinterest pin pack for week of {week_start}...")
    content = generate_pin_pack(week_start)
    save_pin_pack(content, week_start)
    print("Done.")
