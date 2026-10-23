"""
Inkspire Weekly Blog Post Generator
Uses Google Gemini free tier (aistudio.google.com) — no credit card needed.
"""

import os
import time
import json
import random
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
    ("Tattoo Placement Guide: Best Spots for Your First Tattoo", "placement-guide", "Placement", "7 min", "Beginner Guide",
     "https://images.unsplash.com/photo-1565058379802-bbe93b2f703a?auto=format&fit=crop&w=1400&q=80", "tattoo placement guide"),
    ("Watercolour Tattoos: Everything You Need to Know", "watercolour-tattoos", "Style Guide", "8 min", "Style Guide",
     "https://images.unsplash.com/photo-1611501275019-9b5cda994e8d?auto=format&fit=crop&w=1400&q=80", "watercolour tattoo art"),
    ("Traditional vs Neo-Traditional Tattoos: What's the Difference?", "traditional-vs-neo-traditional", "Style Guide", "6 min", "Style Deep-Dive",
     "https://images.unsplash.com/photo-1562155618-e1a8e303fc0a?auto=format&fit=crop&w=1400&q=80", "traditional tattoo style"),
    ("How Much Does a Tattoo Cost? 2025 Pricing Guide", "tattoo-cost-guide", "Advice", "5 min", "Budgeting",
     "https://images.unsplash.com/photo-1598300042247-d088f8ab3a91?auto=format&fit=crop&w=1400&q=80", "tattoo studio pricing"),
    ("Tattoo Ink Colours: Which Last Longest and Why", "tattoo-ink-colours", "Education", "7 min", "Education",
     "https://images.unsplash.com/photo-1590246814883-57c511e0b6d0?auto=format&fit=crop&w=1400&q=80", "colourful tattoo ink"),
    ("Geometric Tattoos: Style Guide and Artist Tips", "geometric-tattoos", "Style Guide", "8 min", "Style Guide",
     "https://images.unsplash.com/photo-1568515045052-f9a854d70bfd?auto=format&fit=crop&w=1400&q=80", "geometric tattoo pattern"),
    ("Japanese Tattoo Style: History, Meanings, and Modern Takes", "japanese-tattoo-guide", "Style Guide", "10 min", "Cultural Guide",
     "https://images.unsplash.com/photo-1579208030886-b937da0925dc?auto=format&fit=crop&w=1400&q=80", "Japanese tattoo irezumi"),
    ("Tattoo Touch-Ups: When, Why, and How Much They Cost", "tattoo-touch-up-guide", "Aftercare", "6 min", "Maintenance",
     "https://images.unsplash.com/photo-1513885535751-8b9238bd345a?auto=format&fit=crop&w=1400&q=80", "tattoo touch up"),
    ("Small Tattoo Ideas That Actually Age Well", "small-tattoo-ideas", "Inspiration", "7 min", "Ideas",
     "https://images.unsplash.com/photo-1596462502278-27bfdc403348?auto=format&fit=crop&w=1400&q=80", "small minimalist tattoo"),
    ("Blackwork Tattoos: The Ultimate Bold Style Guide", "blackwork-tattoo-guide", "Style Guide", "9 min", "Style Guide",
     "https://images.unsplash.com/photo-1571840840042-adf28b70d5ef?auto=format&fit=crop&w=1400&q=80", "blackwork tattoo bold"),
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


def pick_topic():
    used_file = ".github/scripts/used_topics.json"
    try:
        with open(used_file) as f:
            used = json.load(f)
    except FileNotFoundError:
        used = []

    available = [t for t in TOPIC_POOL if t[1] not in used]
    if not available:
        used = []
        available = TOPIC_POOL

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


def save_article(topic, body):
    title, slug, tag, read_time, category, hero_image, hero_alt = topic
    today = datetime.date.today().isoformat()

    front_matter = f"""---
layout: article
title: "{title}"
description: "Complete guide to {title.lower()} — expert tips, recommendations, and everything a tattoo enthusiast needs to know."
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


if __name__ == "__main__":
    print("Generating weekly blog post...")
    topic = pick_topic()
    print(f"Topic: {topic[0]}")
    body = generate_article(topic)
    save_article(topic, body)
    print("Done.")
