from playwright.sync_api import sync_playwright
from urllib.parse import urljoin
from geopy.geocoders import Nominatim
from geopy.exc import (
    GeocoderTimedOut,
    GeocoderServiceError,
)  # Import specific exceptions
import json
import time
import re  # Added for potential string cleaning

BASE_MASS = "https://www.massaudubon.org"
BASE_NATL = "https://www.audubon.org"

# IMPORTANT: Provide a unique user_agent with an identifiable string (e.g., your email or project name)
# This is crucial for Nominatim's usage policy.
geolocator = Nominatim(
    user_agent="YourAudubonEventScraper/1.0 (ondrasek_hanna@wheatoncollege.edu)"
)

# --- Manual Lookup Table (Add more as you encounter consistently failing locations) ---
MANUAL_NATIONAL_AUDUBON_LOCATIONS = {
    # Format: "Scraped Location String": ("Latitude", "Longitude")
    "Audubon Maryland-DC, Philadelphia, PA": (
        "39.952583",
        "-75.165222",
    ),  # Example: Center of Philadelphia
    "Seward Park Audubon Center, Seattle, WA": (
        "47.5599",
        "-122.2222",
    ),  # Example: Coords for Seward Park (approx.)
    "Dogwood Canyon Audubon Center at Cedar Hill, Cedar Hill, TX": (
        "32.5518",
        "-96.9602",
    ),  # Example: Coords for Cedar Hill
    "Montezuma Audubon Center, Savannah, NY": (
        "43.0456",
        "-76.7107",
    ),  # Example: Coords for Savannah, NY
    "Audubon Pennsylvania, Baltimore, MD": (
        "39.290385",
        "-76.612189",
    ),  # Center of Baltimore
    "Audubon Maryland-DC, Baltimore, MD": (
        "39.290385",
        "-76.612189",
    ),  # Center of Baltimore (duplicate entry as above, but good for robust lookup)
    "Greenwich Audubon Center, Greenwich, CT": (
        "41.0180",
        "-73.6190",
    ),  # Example coords for Greenwich, CT
    "Audubon Connecticut, Sharon, CT": (
        "41.8797",
        "-73.5350",
    ),  # Example coords for Sharon, CT
    "Audubon Maryland-DC, Audubon, PA": (
        "40.1215624",
        "-75.4371849",
    ),  # Same as "Audubon Pennsylvania, Audubon, PA"
    # Add any other specific problematic locations from your data
}


def _geocode_location(location_str, attempt_type="original"):
    """
    Helper function to geocode a location string with Nominatim and handle delays/retries.
    """
    print(f"  [GEOCoding] Attempting geocoding '{attempt_type}' for: '{location_str}'")
    try:
        # Nominatim requires a delay between requests
        time.sleep(1.2)  # Increased slightly to be safer than exactly 1 second

        loc = geolocator.geocode(location_str, timeout=10)  # Add a timeout for safety
        if loc:
            print(
                f"  [GEOCoding] Success for '{location_str}': {loc.latitude}, {loc.longitude}"
            )
            return str(loc.latitude), str(loc.longitude)
        else:
            print(f"  [GEOCoding] No results from Nominatim for: '{location_str}'")
            return None, None
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(
            f"  [GEOCoding ERROR] Nominatim service error or timeout for '{location_str}': {e}"
        )
        return None, None
    except Exception as e:
        print(f"  [GEOCoding ERROR] Unexpected error geocoding '{location_str}': {e}")
        return None, None


def get_lat_lon_for_national_audubon_event(location_str):
    """
    Tries to get latitude and longitude for a National Audubon event location
    using multiple strategies.
    """
    if not location_str:
        return None, None

    # 1. Check manual lookup first
    if location_str in MANUAL_NATIONAL_AUDUBON_LOCATIONS:
        print(f"[GEOCoding] Using manual lookup for: '{location_str}'")
        return MANUAL_NATIONAL_AUDUBON_LOCATIONS[location_str]

    # 2. Try geocoding the original location string
    lat, lon = _geocode_location(location_str, "original")
    if lat is not None:
        return lat, lon

    # 3. Try simplifying the location string (e.g., "City, State")
    # This regex attempts to find "Something, City, State" or "City, State" patterns
    match_city_state = re.search(r"([A-Za-z\s\.-]+),\s*([A-Z]{2})$", location_str)
    if match_city_state:
        simpler_location_str = (
            f"{match_city_state.group(1).strip()}, {match_city_state.group(2).strip()}"
        )
        if simpler_location_str != location_str:  # Avoid redundant geocode call
            lat, lon = _geocode_location(simpler_location_str, "city, state")
            if lat is not None:
                return lat, lon

    # 4. Try stripping common prefixes/suffixes that might confuse geocoder
    # Example: "Audubon Center at Debs Park, Los Angeles, CA" -> "Debs Park, Los Angeles, CA"
    # Example: "John James Audubon Center, Audubon, PA" -> "Audubon, PA"
    cleaned_location_str = (
        location_str.replace("Audubon Center at ", "")
        .replace("Audubon Center, ", "")
        .strip()
    )
    cleaned_location_str = cleaned_location_str.replace(
        "Audubon ", ""
    ).strip()  # Remove standalone "Audubon"
    if (
        cleaned_location_str != location_str
        and cleaned_location_str != simpler_location_str
    ):  # Prevent redundant checks
        lat, lon = _geocode_location(cleaned_location_str, "cleaned")
        if lat is not None:
            return lat, lon

    # 5. If all else fails, return None, None
    print(
        f"[GEOCoding] Ultimately failed to geocode: '{location_str}' after all attempts."
    )
    return None, None


def fetch_events_with_playwright(pages=3):
    print("[DEBUG] Launching browser for Mass Audubon...")

    events = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for page_num in range(1, pages + 1):
            url = (
                BASE_MASS
                + f"/programs?prg%5Baudiences%5D%5B0%5D=864&prg%5Baudiences%5D%5B1%5D=865&page={page_num}"
            )
            print(f"[DEBUG] Navigating to {url}")
            page.goto(url, timeout=60000)
            page.wait_for_timeout(5000)

            event_cards = page.locator(".event-card")
            count = event_cards.count()
            print(f"[DEBUG] Found {count} Mass Audubon events on page {page_num}.")

            for i in range(count):
                try:
                    card = event_cards.nth(i)

                    title = card.locator(".event-card__content__title").inner_text()
                    date = card.locator(".event-card__content__date").inner_text()
                    age = card.locator(".event-card__content__ages").inner_text()

                    place_el = card.locator(".event-card__content__place")
                    lat = place_el.get_attribute("data-latitude")
                    lon = place_el.get_attribute("data-longitude")
                    place_parts = place_el.locator(".ezstring-field").all_inner_texts()
                    place = ", ".join(
                        [part.strip() for part in place_parts if part.strip()]
                    )
                    link_el = card.locator("a").first
                    link = link_el.get_attribute("href") if link_el else ""
                    full_link = urljoin(BASE_MASS, link) if link else ""

                    events.append(
                        {
                            "title": title.strip(),
                            "date": date.strip(),
                            "ages": age.strip(),
                            "location": place,
                            "latitude": lat,
                            "longitude": lon,
                            "url": full_link,
                        }
                    )
                except Exception as e:
                    print(
                        f"[WARN] Error parsing Mass Audubon card {i + 1} on page {page_num}: {e}"
                    )

        browser.close()
    return events


def fetch_national_audubon_events(pages=3):
    print("[DEBUG] Launching browser for National Audubon...")
    events = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for page_num in range(1, pages + 1):
            url = f"https://www.audubon.org/events?view_type=row&page={page_num}"
            print(f"[DEBUG] Navigating to {url}")
            page.goto(url, timeout=60000)
            page.wait_for_timeout(4000)

            cards = page.locator(".event-card-item")
            count = cards.count()
            print(f"[DEBUG] Found {count} National Audubon events on page {page_num}.")

            for i in range(count):
                try:
                    card = cards.nth(i)

                    link_el = card.locator("a.card-link")
                    title = link_el.inner_text()
                    href = link_el.get_attribute("href")
                    url = urljoin("https://www.audubon.org", href)

                    time_text = card.locator(
                        ".event-card-item-header__time--time"
                    ).inner_text()

                    months = card.locator(
                        ".event-card-item-header__month span"
                    ).all_inner_texts()
                    month = [m.strip() for m in months if m.strip()][-1]
                    day = (
                        card.locator(".event-card-item-header__date span")
                        .nth(0)
                        .inner_text()
                    )
                    date = f"{month} {day}"

                    location = (
                        card.locator(".event-card-item-location").inner_text().strip()
                    )

                    # --- Geocoding for National Audubon events (Improved) ---
                    latitude, longitude = get_lat_lon_for_national_audubon_event(
                        location
                    )
                    # --- End of Geocoding improvement ---

                    events.append(
                        {
                            "title": title.strip(),
                            "date": f"{date} — {time_text}",
                            "ages": "All ages",
                            "location": location,
                            "latitude": latitude,
                            "longitude": longitude,
                            "url": url,
                        }
                    )

                except Exception as e:
                    print(
                        f"[WARN] Error parsing National Audubon card {i + 1} on page {page_num}: {e}"
                    )

        browser.close()
    return events


if __name__ == "__main__":
    print("[DEBUG] Starting combined scrape...")

    try:
        mass_events = fetch_events_with_playwright(pages=3)
        natl_events = fetch_national_audubon_events(pages=3)

        all_events = mass_events + natl_events

        with open("audubon_events.json", "w", encoding="utf-8") as f:
            json.dump(all_events, f, ensure_ascii=False, indent=2)

        print(f"[DEBUG] Saved {len(all_events)} total events to audubon_events.json")

    except Exception as e:
        print("[ERROR]", str(e))
