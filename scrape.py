from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import time
import random

BASE_URL = "https://tut4it.com/topics/management-training/"

all_titles = []
debug_printed = False

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 800},
        locale="en-US",
    )
    page = context.new_page()

    for n in range(1, 21):
        url = BASE_URL if n == 1 else f"{BASE_URL}page/{n}/"
        print(f"Fetching page {n}: {url}")

        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=30000)
            status = resp.status if resp else "?"
            print(f"  Status: {status}")

            if status != 200:
                print(f"  Skipping page {n} (non-200)")
                time.sleep(random.uniform(1.5, 3.0))
                continue

            # Wait a moment for any JS rendering
            page.wait_for_timeout(1500)

            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

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
                print("  No titles found — printing HTML snippet for debugging:")
                body = soup.find("body")
                print(str(body)[:3000] if body else html[:3000])
                debug_printed = True

            if titles:
                all_titles.extend(titles)
                print(f"  Found {len(titles)} titles (total so far: {len(all_titles)})")
            else:
                print(f"  No titles found on page {n}")

        except Exception as e:
            print(f"  Error on page {n}: {e}")

        time.sleep(random.uniform(1.5, 3.0))

    browser.close()

print(f"\nTotal titles collected: {len(all_titles)}")

with open("courses.txt", "w", encoding="utf-8") as f:
    for title in all_titles:
        f.write(title + "\n")

with open("courses.json", "w", encoding="utf-8") as f:
    json.dump(all_titles, f, ensure_ascii=False, indent=2)

print("Written to courses.txt and courses.json")
