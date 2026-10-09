"""
Inkspire Weekly Blog Post Generator
Generates a new Jekyll article targeting USA tattoo audience.
Runs every Monday via GitHub Actions.
"""

import anthropic
import datetime
import os
import re
import json
import random

client = anthropic.Anthropic()

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
    {"name": "Hustle Butter Deluxe", "query": "hustle+butter+tattoo+aftercare", "desc": "The professional standard vegan aftercare balm."},
    {"name": "Saniderm Healing Bandage", "query": "saniderm+tattoo+bandage", "desc": "Second-skin film for the critical healing phase."},
    {"name": "Tattoo Sunscreen SPF 50", "query": "tattoo+sunscreen+spf+50", "desc": "UV protection formulated for tattooed skin."},
    {"name": "Tattoo Goo Aftercare Lotion", "query": "tattoo+goo+aftercare+lotion", "desc": "Long-term moisturiser to keep ink vibrant."},
    {"name": "H2Ocean Aftercare Spray", "query": "h2ocean+tattoo+aftercare+spray", "desc": "Piercing and tattoo aftercare spray with sea salt."},
]

SYSTEM_PROMPT = """You are a professional tattoo content writer for Inkspire, a US-focused tattoo inspiration website.
Write engaging, authoritative articles targeting a USA audience aged 18-35 who love tattoos.
Your writing style: confident, knowledgeable, conversational — like a trusted tattoo artist giving advice.
Include specific tips that feel insider and useful. Always write in HTML suitable for Jekyll.
Amazon affiliate tag: """ + AFFILIATE_TAG


def pick_topic():
    """Pick a topic we haven't used recently (simple: pick randomly from pool)."""
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
    # Keep only last 8 to allow recycling
    used = used[-8:]

    os.makedirs(os.path.dirname(used_file), exist_ok=True)
    with open(used_file, "w") as f:
        json.dump(used, f)

    return topic


def generate_article(topic):
    title, slug, tag, read_time, category, hero_image, hero_alt = topic
    product = random.choice(AMAZON_PRODUCTS)

    prompt = f"""Write a complete, SEO-optimised article for Inkspire about: "{title}"

Requirements:
- 700-900 words of real, useful content
- Target keyword: "{title.lower()}"
- Include 4-6 H2 headings
- One <div class="tip-box"> with a pro tip
- One product callout using this exact HTML structure:
<div class="product-callout">
  <img src="https://images.pexels.com/photos/18748260/pexels-photo-18748260.jpeg?auto=compress&cs=tinysrgb&w=200" alt="{product['name']}">
  <div class="product-callout-body">
    <div class="product-callout-name">{product['name'].upper()}</div>
    <div class="product-callout-desc">{product['desc']}</div>
    <a href="https://www.amazon.com/s?k={product['query']}&tag={AFFILIATE_TAG}" target="_blank" rel="noopener nofollow" class="btn-buy">Shop on Amazon →</a>
  </div>
</div>
- End with an encouraging closing paragraph
- Output ONLY the HTML body content — no doctype, no html/head/body tags, no front matter
- Use <p>, <h2>, <h3>, <ul>, <li> tags
- Do not add inline styles or class names except tip-box and product-callout as shown above"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text


def save_article(topic, body):
    title, slug, tag, read_time, category, hero_image, hero_alt = topic
    today = datetime.date.today().isoformat()

    front_matter = f"""---
layout: article
title: "{title}"
description: "Read our complete guide to {title.lower()} — expert tips, product recommendations, and everything a tattoo enthusiast needs to know."
article_tag: "{tag}"
read_time: "{read_time}"
category: "{category}"
hero_image: "{hero_image}"
hero_alt: "{hero_alt}"
date: {today}
updated: "{today}"
---

"""

    filename = f"{slug}.html"
    filepath = filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(front_matter + body)

    print(f"Created article: {filepath}")
    return filename


def update_homepage_blog_grid(filename, title, tag, read_time):
    """Append a blog card to the homepage blog grid (optional — only if index.html exists)."""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            content = f.read()
        print(f"Homepage exists — you may want to manually add a card for: {title}")
    except FileNotFoundError:
        pass


if __name__ == "__main__":
    print("Inkspire: generating weekly blog post...")
    topic = pick_topic()
    print(f"Topic: {topic[0]}")
    body = generate_article(topic)
    filename = save_article(topic, body)
    update_homepage_blog_grid(filename, topic[0], topic[2], topic[3])
    print("Done.")
