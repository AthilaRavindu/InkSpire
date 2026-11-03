"""
Inkspire Weekly Blog Post Generator
Uses Google Gemini free tier (aistudio.google.com) — no credit card needed.
"""

import os
import re
import time
import json
import random
import datetime
import requests
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
                print(f"Generated using {model_name}")
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

AFFILIATE_TAG = "inkspiretatto-20"

TOPIC_POOL = [
    # (title, slug, article_tag, read_time, category, hero_image, hero_alt)
    #
    # Six of the images this pool originally carried had silently become
    # photographs of something else -- the Japanese guide's hero was a plate of
    # fish and chips -- while still returning HTTP 200. Every URL below has now
    # been opened and looked at. Do not add one you have not viewed.
    ("Tattoo Placement Guide: Best Spots for Your First Tattoo", "placement-guide", "Placement", "7 min", "Beginner Guide",
     "https://images.unsplash.com/photo-1542727365-19732a80dcfd?auto=format&fit=crop&w=1400&q=80", "fine line tattoo on a forearm"),
    ("Watercolour Tattoos: Everything You Need to Know", "watercolour-tattoos", "Style Guide", "8 min", "Inspiration",
     "https://images.unsplash.com/photo-1611501275019-9b5cda994e8d?auto=format&fit=crop&w=1400&q=80", "watercolour tattoo art"),
    ("Traditional vs Neo-Traditional Tattoos: What's the Difference?", "traditional-vs-neo-traditional", "Style Guide", "6 min", "Style Deep-Dive",
     "https://live.staticflickr.com/65535/52561627575_ff94a01718_b.jpg", "traditional colour tattoos"),
    ("How Much Does a Tattoo Cost? 2025 Pricing Guide", "tattoo-cost-guide", "Advice", "5 min", "Budgeting",
     "https://images.unsplash.com/photo-1598300042247-d088f8ab3a91?auto=format&fit=crop&w=1400&q=80", "tattoo studio pricing"),
    ("Tattoo Ink Colours: Which Last Longest and Why", "tattoo-ink-colours", "Education", "7 min", "Ink & Colour",
     "https://images.unsplash.com/photo-1562379825-415aea84ebcf?auto=format&fit=crop&w=1400&q=80", "colourful tattoo ink"),
    ("Geometric Tattoos: Style Guide and Artist Tips", "geometric-tattoos", "Style Guide", "8 min", "Design",
     "https://images.unsplash.com/photo-1594812332797-bec39ee15b47?auto=format&fit=crop&w=1400&q=80", "geometric back tattoo"),
    ("Japanese Tattoo Style: History, Meanings and Modern Takes", "japanese-tattoo-guide", "Style Guide", "10 min", "Cultural Guide",
     "https://images.unsplash.com/photo-1568515045052-f9a854d70bfd?auto=format&fit=crop&w=1400&q=80", "detailed ornamental sleeve"),
    ("Tattoo Touch-Ups: When, Why, and How Much They Cost", "tattoo-touch-up-guide", "Aftercare", "6 min", "Maintenance",
     "https://live.staticflickr.com/7548/16058781110_029032b185_b.jpg", "artist reworking a tattoo"),
    ("Small Tattoo Ideas That Actually Age Well", "small-tattoo-ideas", "Inspiration", "7 min", "Ideas",
     "https://images.unsplash.com/photo-1596462502278-27bfdc403348?auto=format&fit=crop&w=1400&q=80", "small minimalist tattoo"),
    ("Blackwork Tattoos: The Ultimate Bold Style Guide", "blackwork-tattoo-guide", "Style Guide", "9 min", "Bold Styles",
     "https://images.unsplash.com/photo-1552627019-947c3789ffb5?auto=format&fit=crop&w=1400&q=80", "black and grey tattoo work"),
    ("Does Getting a Tattoo Hurt? Pain Chart by Body Part", "tattoo-pain-chart", "Advice", "7 min", "First Timers",
     "https://images.unsplash.com/photo-1565058379802-bbe93b2f703a?auto=format&fit=crop&w=1400&q=80", "person getting tattooed"),
    ("How to Prepare for Your First Tattoo Appointment", "first-tattoo-prep", "Advice", "6 min", "First Timers",
     "https://live.staticflickr.com/65535/52664878201_c4175f047d_b.jpg", "tattooed person waiting"),
    ("Tattoo Removal and Cover-Ups: What Your Options Are", "tattoo-coverup-removal", "Education", "8 min", "Fixing Mistakes",
     "https://live.staticflickr.com/65535/52302686837_bddd4d7f59_b.jpg", "dense colourful leg tattoos"),
    ("Matching Tattoos: Ideas for Couples, Friends and Family", "matching-tattoos", "Inspiration", "6 min", "Ideas",
     "https://images.unsplash.com/photo-1701269395744-32e3c1d11645?auto=format&fit=crop&w=1400&q=80", "tattooed person portrait"),
    ("Sleeve Tattoos: Planning a Full Arm That Works Together", "sleeve-tattoo-guide", "Style Guide", "10 min", "Big Pieces",
     "https://images.unsplash.com/photo-1568515045052-f9a854d70bfd?auto=format&fit=crop&w=1400&q=80", "full tattoo sleeve in progress"),
    ("Script and Lettering Tattoos: Fonts, Placement and Mistakes", "script-tattoo-guide", "Style Guide", "7 min", "Lettering",
     "https://images.unsplash.com/photo-1608270788029-458f9705a0b9?auto=format&fit=crop&w=1400&q=80", "lettering tattoo on a forearm"),
]

AMAZON_PRODUCTS = [
    {"name": "Hustle Butter Deluxe", "query": "hustle+butter+tattoo+aftercare",
     "img": "https://images.pexels.com/photos/18748260/pexels-photo-18748260.jpeg?auto=compress&cs=tinysrgb&w=200",
     "desc": "The professional standard vegan aftercare balm."},
    {"name": "Saniderm Healing Bandage", "query": "saniderm+tattoo+bandage",
     "img": "https://images.pexels.com/photos/5721552/pexels-photo-5721552.jpeg?auto=compress&cs=tinysrgb&w=200",
     "desc": "Second-skin film for the critical healing phase."},
    {"name": "Tattoo Sunscreen SPF 50", "query": "tattoo+sunscreen+spf+50",
     "img": "https://images.pexels.com/photos/16615433/pexels-photo-16615433.jpeg?auto=compress&cs=tinysrgb&w=200",
     "desc": "UV protection formulated for tattooed skin."},
    {"name": "Tattoo Goo Aftercare Lotion", "query": "tattoo+goo+aftercare+lotion",
     "img": "https://images.pexels.com/photos/9775222/pexels-photo-9775222.jpeg?auto=compress&cs=tinysrgb&w=200",
     "desc": "Long-term moisturiser to keep ink vibrant."},
]


def image_is_live(url):
    """Catches a retired image, but not a repurposed one.

    A status check alone is not enough: some hosts answer 200 with a block page
    or placeholder rather than an image, so the content type is checked too.
    Neither check can tell whether the photo still shows a tattoo -- that is why
    every URL in this file was opened and looked at by hand.
    """
    try:
        response = requests.head(url, timeout=15, allow_redirects=True)
        if response.status_code != 200:
            return False
        return response.headers.get("Content-Type", "").startswith("image/")
    except Exception:
        return True  # a network blip should not block the weekly post


# Every URL in TOPIC_POOL and below has been opened and looked at. That is the
# only check that works here. Keyword search was tried and abandoned: the
# public-domain pools return a canoe for "traditional tattoo", a digital skull
# for "tattoo artist" and a basket of sweet potatoes for "getting a tattoo".
FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1565058379802-bbe93b2f703a?auto=format&fit=crop&w=1400&q=80",
    "https://images.unsplash.com/photo-1552627019-947c3789ffb5?auto=format&fit=crop&w=1400&q=80",
    "https://live.staticflickr.com/65535/52302686837_bddd4d7f59_b.jpg",
    "https://live.staticflickr.com/7548/16058781110_029032b185_b.jpg",
]


def resolve_hero(topic):
    """Keep the topic's verified image, or swap in a fallback if it has rotted."""
    title, slug, tag, read_time, category, hero_image, hero_alt = topic
    if image_is_live(hero_image):
        return topic
    pool = random.sample(FALLBACK_IMAGES, len(FALLBACK_IMAGES))
    url = next((u for u in pool if image_is_live(u)), pool[0])
    print(f"Hero for '{slug}' has rotted — substituting a fallback")
    return (title, slug, tag, read_time, category, url, hero_alt)


def pick_topic():
    used_file = ".github/scripts/used_topics.json"
    try:
        with open(used_file) as f:
            used = json.load(f)
    except FileNotFoundError:
        used = []

    # used_topics.json only remembers what this script generated. Four pool slugs
    # were also written by hand and published, so without the exists() check a
    # regenerated article would silently overwrite the live, edited version.
    available = [t for t in TOPIC_POOL
                 if t[1] not in used and not os.path.exists(f"{t[1]}.html")]
    if not available:
        used = []
        available = [t for t in TOPIC_POOL if not os.path.exists(f"{t[1]}.html")]
    if not available:
        raise SystemExit("Every pool topic is already published — add new topics.")

    topic = random.choice(available)

    used.append(topic[1])
    used = used[-8:]

    os.makedirs(os.path.dirname(used_file), exist_ok=True)
    with open(used_file, "w") as f:
        json.dump(used, f)

    return topic


INTERNAL_LINKS = [
    ("aftercare-guide.html", "tattoo aftercare guide"),
    ("fine-line-guide.html", "fine line tattoo guide"),
    ("find-tattoo-artist.html", "how to find a tattoo artist"),
    ("tattoo-trends-2025.html", "2025 tattoo trends"),
]


def generate_article(topic):
    title, slug, tag, read_time, category, hero_image, hero_alt = topic
    product = random.choice(AMAZON_PRODUCTS)
    links = random.sample(INTERNAL_LINKS, 2)
    link_text = "\n".join(f'  <a href="/InkSpire/{url}">{anchor}</a>' for url, anchor in links)

    prompt = f"""You are a professional tattoo content writer for Inkspire, a US tattoo website for an audience aged 18-35.
Write a complete, SEO-optimised article about: "{title}"

Requirements:
- 700-900 words of genuinely useful content
- Use the keyword "{title.lower()}" naturally in the first paragraph as PLAIN TEXT, never as a link
- NEVER invent, guess, or make up any URL or domain name. The ONLY links allowed in the
  entire article are the Amazon product link below and these two internal links, each used
  once, placed naturally where the topic fits:
{link_text}
- 4-6 H2 headings using <h2> tags
- One tip box using EXACTLY this HTML:
<div class="tip-box"><strong>Pro Tip</strong><p>your tip here</p></div>
- One product callout using EXACTLY this HTML (do not change class names):
<div class="product-callout">
  <img src="{product['img']}" alt="{product['name']}">
  <div class="product-callout-body">
    <div class="product-callout-name">{product['name'].upper()}</div>
    <div class="product-callout-desc">{product['desc']}</div>
    <a href="https://www.amazon.com/s?k={product['query']}&tag={AFFILIATE_TAG}" target="_blank" rel="noopener nofollow" class="btn-buy">Shop on Amazon →</a>
  </div>
</div>
- Writing style: confident, knowledgeable, conversational — like a trusted tattoo artist giving advice
- Output ONLY the HTML body content — no doctype, html, head, body tags, no front matter, no markdown code fences
- Use only <p>, <h2>, <h3>, <ul>, <li> tags plus the two special components above
- Do not add inline styles"""

    return generate_with_retry(prompt)


def save_article(topic, body, description):
    title, slug, tag, read_time, category, hero_image, hero_alt = topic
    today = datetime.date.today().isoformat()

    front_matter = f"""---
layout: article
title: "{title}"
description: "{description.replace('"', "'")}"
article_tag: "{tag}"
read_time: "{read_time}"
category: "{category}"
hero_image: "{hero_image}"
hero_alt: "{hero_alt}"
date: {today}
updated: "{today}"
---

"""

    with open(f"{slug}.html", "w", encoding="utf-8") as f:
        f.write(front_matter + body)

    print(f"Created: {slug}.html")


def write_card_copy(title, body):
    """An article's opening paragraph is a narrative warm-up, not a summary, so
    slicing it produced cards that trailed off mid-sentence. Ask for purpose-
    written copy instead and fall back to a clean slice only if parsing fails."""
    plain = re.sub(r"<[^>]+>", " ", body)
    plain = re.sub(r"\s+", " ", plain).strip()[:2500]

    prompt = f"""Here is a tattoo article titled "{title}":

{plain}

Write two things about it, for a site called Inkspire.

EXCERPT: one complete sentence, 90-120 characters, saying what the reader
will get out of the article. Concrete and specific — name the actual things
covered. No ellipsis, no trailing off, never repeat the title back.
Match this style: "Day-by-day healing instructions, best products, what to
avoid, and how to keep your ink vibrant for life."

DESCRIPTION: one sentence, 140-160 characters, for the Google search result.
Natural English a person would read aloud. Do not stuff the title into it.

Reply in EXACTLY this format and nothing else:
EXCERPT: [text]
DESCRIPTION: [text]"""

    try:
        reply = generate_with_retry(prompt)
        excerpt = re.search(r"^EXCERPT:\s*(.+)$", reply, re.MULTILINE)
        description = re.search(r"^DESCRIPTION:\s*(.+)$", reply, re.MULTILINE)
        if excerpt and description:
            return excerpt.group(1).strip().strip('"'), description.group(1).strip().strip('"')
        print("Card copy came back malformed — falling back")
    except Exception as e:
        print(f"Card copy generation failed ({e}) — falling back")

    first = re.search(r"<p>(.*?)</p>", body, re.DOTALL)
    text = re.sub(r"<[^>]+>", "", first.group(1)).strip() if first else ""
    text = re.sub(r"\s+", " ", text)
    if len(text) > 140:
        text = text[:140].rsplit(" ", 1)[0].rstrip(",;:") + "."
    return (text or f"A complete guide to {title.lower()}."), text[:155]


def add_to_homepage(topic, excerpt, keep=6):
    """Without a homepage link a new article is an orphan page: readers cannot
    reach it and search engines heavily discount it."""
    title, slug, tag, read_time, category, hero_image, hero_alt = topic

    with open("index.html", encoding="utf-8") as f:
        html = f.read()

    if f'href="{slug}.html"' in html:
        print(f"{slug}.html already linked from homepage")
        return

    thumb = hero_image.replace("w=1400", "w=600&h=340").replace("_b.jpg", "_z.jpg")
    meta_bits = f'<span>{read_time}</span>'
    if category.strip().lower() != tag.strip().lower():
        meta_bits += f'<span>·</span><span>{category}</span>'

    card = (
        '      <article class="blog-card">\n'
        f'        <div class="blog-thumb"><img src="{thumb}" alt="{hero_alt}" loading="lazy"></div>\n'
        '        <div class="blog-body">\n'
        f'          <div class="blog-tag">{tag}</div>\n'
        f'          <h3 class="blog-title">{title.upper()}</h3>\n'
        f'          <p class="blog-excerpt">{excerpt}</p>\n'
        f'          <div class="blog-footer"><div class="blog-meta">{meta_bits}</div>'
        f'<a href="{slug}.html" class="blog-read">Read →</a></div>\n'
        '        </div>\n'
        '      </article>\n'
    )

    anchor = '<div class="blog-grid">\n'
    if anchor not in html:
        print("Could not find blog grid on homepage — skipping")
        return
    html = html.replace(anchor, anchor + card, 1)

    grid = re.search(r'(<div class="blog-grid">\n)(.*?)(^    </div>)',
                     html, re.DOTALL | re.MULTILINE)
    if grid:
        cards = re.findall(r'      <article class="blog-card">.*?      </article>\n',
                           grid.group(2), re.DOTALL)
        if len(cards) > keep:
            html = html[:grid.start(2)] + "".join(cards[:keep]) + html[grid.end(2):]
            print(f"Homepage trimmed to the {keep} newest guides")

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Added {slug}.html to homepage")


if __name__ == "__main__":
    print("Generating weekly blog post...")
    topic = resolve_hero(pick_topic())
    print(f"Topic: {topic[0]}")
    body = generate_article(topic)
    excerpt, description = write_card_copy(topic[0], body)
    print(f"Excerpt: {excerpt}")
    save_article(topic, body, description)
    add_to_homepage(topic, excerpt)
    print("Done.")
