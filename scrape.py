from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import requests
import json
import time
import random

BASE_URL = "https://tut4it.com/topics/management-training/"

# Step 1: open real browser, let user solve CF challenge, steal the cookies
print("Opening browser — solve the Cloudflare challenge, then come back here and press Enter.")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
    input("Press Enter once the page has fully loaded past the challenge...")
    cookies = context.cookies()
    browser.close()

# Step 2: build a requests session using the stolen cookies
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://tut4it.com/",
})
for c in cookies:
    session.cookies.set(c["name"], c["value"], domain=c.get("domain", "tut4it.com"))

cf_clearance = next((c["value"] for c in cookies if c["name"] == "cf_clearance"), None)
print(f"cf_clearance cookie: {'found' if cf_clearance else 'NOT FOUND — challenge may not have been solved'}")

# Step 3: scrape all 20 pages with requests
all_titles = []
debug_printed = False

for n in range(1, 21):
    url = BASE_URL if n == 1 else f"{BASE_URL}page/{n}/"
    print(f"Fetching page {n}: {url}")

    try:
        resp = session.get(url, timeout=15)
        print(f"  Status: {resp.status_code}")

        if resp.status_code != 200:
            print(f"  Skipping (non-200)")
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        titles = []

        for sel in [
            "h2.post-title", "h2.entry-title", "h3.post-title", "h3.entry-title",
            ".post-title", ".entry-title", "article h2", "article h3",
            ".course-title", ".item-title", "h2 a", "h3 a",
        ]:
            elements = soup.select(sel)
            if elements:
                titles = [el.get_text(strip=True) for el in elements if el.get_text(strip=True)]
                print(f"  Selector '{sel}' matched {len(titles)} titles")
                break

        if not titles and not debug_printed:
            print("  No titles found — HTML snippet:")
            body = soup.find("body")
            print(str(body)[:3000] if body else resp.text[:3000])
            debug_printed = True

        if titles:
            all_titles.extend(titles)
            print(f"  Found {len(titles)} (total: {len(all_titles)})")
        else:
            print(f"  No titles found on page {n}")

    except Exception as e:
        print(f"  Error: {e}")

    time.sleep(random.uniform(1.0, 2.0))

print(f"\nTotal titles collected: {len(all_titles)}")

with open("courses.txt", "w", encoding="utf-8") as f:
    for title in all_titles:
        f.write(title + "\n")

with open("courses.json", "w", encoding="utf-8") as f:
    json.dump(all_titles, f, ensure_ascii=False, indent=2)

print("Written to courses.txt and courses.json")
