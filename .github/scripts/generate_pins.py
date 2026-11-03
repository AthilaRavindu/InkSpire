"""
Inkspire Pinterest Pin Pack Generator
Uses Google Gemini free tier.
Generates 14 ready-to-post pins a week — two a day, each with an AI image prompt.
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

# Each theme is paired with the article it actually sends readers to, so the pin
# copy and the destination page always match. Three of these point at guides
# written specifically to catch the account's best-performing pins.
DAILY_THEMES = [
    ("Monday", "the meanings behind symbolic tattoos — doves, lions, broken chains, roses",
     "tattoo-symbolism-meanings.html"),
    ("Tuesday", "the fine line tattoo style — delicate, minimalist, detailed work",
     "fine-line-guide.html"),
    ("Wednesday", "tattoo aftercare and how to keep ink looking fresh long-term",
     "aftercare-guide.html"),
    ("Thursday", "back tattoos — placement, pain levels, and the healing you cannot reach",
     "back-tattoo-guide.html"),
    ("Friday", "how to find, vet and book the right tattoo artist",
     "find-tattoo-artist.html"),
    ("Saturday", "Japanese irezumi — dragons, koi, tigers, and what the motifs mean",
     "japanese-tattoo-guide.html"),
    ("Sunday", "trending tattoo designs in the USA right now",
     "tattoo-trends-2025.html"),
]

# Two pins a day, in the two formats that actually performed on the account.
# Pins carrying short lettering took the top impression slots; the one on-body
# photograph took more clicks and saves than anything else posted.
PIN_FORMATS = [
    ("Design Card",
     "a flat tattoo design presented as artwork, with a SHORT phrase of three to five "
     "words worked into the composition as part of the design"),
    ("On Body",
     "a realistic photograph of the finished tattoo on a person, showing the placement "
     "on the body, with no text anywhere in the image"),
]


def pin_link(article_page: str, week_start: datetime.date) -> str:
    """Pinterest's mobile app usually strips the referrer, so pin clicks land in
    Analytics as "direct" and the pins look like they did nothing. The UTM tags
    survive that and keep the traffic attributed to Pinterest."""
    return (f"{SITE_URL}/{article_page}"
            f"?utm_source=pinterest&utm_medium=social"
            f"&utm_campaign=pins-{week_start.isoformat()}")


def build_prompt(pin_date, theme, format_name, format_brief):
    if format_name == "Design Card":
        text_rule = ("Work a short phrase of three to five words into the design itself, "
                     "and state the exact words in quotes.")
    else:
        text_rule = "State explicitly that the image contains no text, no lettering and no watermark."

    return f"""You are a Pinterest strategist writing for Inkspire, a tattoo inspiration site targeting USA tattoo fans aged 18-35.

Write ONE Pinterest pin for {pin_date.strftime('%A %B %d, %Y')}.
Theme: {theme}
Pin format: {format_brief}

Rules for the copy:
- Title: max 100 characters, strong curiosity hook
- Description: 150-250 characters, ending in 4-5 hashtags mixing broad (#tattoo #tattooinspo) with niche ones
- The title and description must promise ONLY what the theme covers, because that is
  what the linked page delivers. Never tease a different topic in the call to action.
- Board: pick one of Tattoo Ideas | Tattoo Aftercare | Tattoo Styles | Tattoo Inspiration | Fine Line Tattoos

Rules for the image prompt, which is fed to an AI image generator:
- Write it as one flowing paragraph of 40-70 words, not a list of tags.
- Vertical 2:3 composition, since Pinterest crops anything wider.
- Name the tattoo style, the subject, the body placement, the lighting and the background.
- Specify black and grey, or a named limited palette. Never just say "colourful".
- {text_rule}
- Do not name any real artist, studio, brand or celebrity.

Reply in EXACTLY this format, no extra text:
TITLE: [title]
DESCRIPTION: [description + hashtags]
BOARD: [board name]
IMAGE PROMPT: [the image generation prompt]"""


def generate_pin_pack(week_start: datetime.date) -> str:
    header = [
        f"# Inkspire Pin Pack — Week of {week_start.isoformat()}",
        "",
        "_Two pins a day. Generate the image from IMAGE PROMPT, then paste the rest into_",
        "_pinterest.com/content/scheduled. Post the two a few hours apart, not together._",
        "",
        "_Paste the whole URL including the `?utm_...` part — that is what attributes",
        "the traffic to Pinterest instead of burying it under 'direct'._",
        "",
        "---",
        "",
    ]
    output = "\n".join(header)

    for i, (day_name, theme, article_page) in enumerate(DAILY_THEMES):
        pin_date = week_start + datetime.timedelta(days=i)
        article_link = pin_link(article_page, week_start)
        output += f"# {day_name} — {pin_date.strftime('%B %d')}\n\n"

        for format_name, format_brief in PIN_FORMATS:
            pin_text = generate_with_retry(
                build_prompt(pin_date, theme, format_name, format_brief))
            output += f"### {format_name}\n\n"
            output += pin_text.strip() + "\n"
            output += f"URL: {article_link}\n\n"
            time.sleep(5)  # stay under the free-tier rate limit

        output += "---\n\n"

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
