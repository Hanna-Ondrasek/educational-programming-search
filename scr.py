from playwright.sync_api import sync_playwright
from urllib.parse import urljoin
import json

BASE = "https://www.massaudubon.org"


def fetch_events_with_playwright(pages=3):  # set how many pages you want to scrape
    print("[DEBUG] Launching browser...")

    events = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for page_num in range(1, pages + 1):
            url = (
                BASE
                + f"/programs?prg%5Baudiences%5D%5B0%5D=864&prg%5Baudiences%5D%5B1%5D=865&page={page_num}"
            )
            print(f"[DEBUG] Navigating to {url}")
            page.goto(url, timeout=60000)
            page.wait_for_timeout(5000)  # JS wait

            print(f"[DEBUG] Page {page_num} loaded. Locating event cards...")
            event_cards = page.locator(".event-card")
            count = event_cards.count()
            print(f"[DEBUG] Found {count} event cards on page {page_num}.")

            for i in range(count):
                try:
                    card = event_cards.nth(i)

                    title = card.locator(".event-card__content__title").inner_text(
                        timeout=2000
                    )
                    date = card.locator(".event-card__content__date").inner_text(
                        timeout=2000
                    )
                    age = card.locator(".event-card__content__ages").inner_text(
                        timeout=2000
                    )

                    place_el = card.locator(".event-card__content__place")
                    lat = place_el.get_attribute("data-latitude")
                    lon = place_el.get_attribute("data-longitude")
                    place_parts = place_el.locator(".ezstring-field").all_inner_texts()
                    place = ", ".join(
                        [part.strip() for part in place_parts if part.strip()]
                    )
                    link_el = card.locator("a").first
                    link = link_el.get_attribute("href") if link_el else ""
                    full_link = urljoin(BASE, link) if link else ""

                    events.append(
                        {
                            "title": title.strip(),
                            "date": date.strip(),
                            "ages": age.strip(),
                            "location": place,
                            "latitude": lat,
                            "longitude": lon,
                            "url": full_link,  # new
                        }
                    )
                except Exception as e:
                    print(f"[WARN] Error parsing card {i + 1} on page {page_num}: {e}")

        browser.close()
        # Save to JSON
        with open("audubon_events.json", "w", encoding="utf-8") as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
        print("[DEBUG] Saved to audubon_events.json")

    return events


if __name__ == "__main__":
    print("[DEBUG] Script started.")
    try:
        events = fetch_events_with_playwright(pages=3)  # scrape first 3 pages

        if not events:
            print("[DEBUG] No events found.")
        else:
            print(f"[DEBUG] Displaying {len(events)} events:\n")
            for e in events:
                print(f"{e['date']} — {e['title']} ({e['ages']})")
                print(
                    f"Location: {e['location']} (Lat: {e['latitude']}, Lon: {e['longitude']})\n"
                )
    except Exception as e:
        print("[ERROR]", str(e))
