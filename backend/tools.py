import re
import json
import urllib.request
from urllib.parse import quote_plus

COST_RANGES = {
    "plumbing": (100, 450),
    "electrical": (120, 500),
    "hvac": (150, 900),
    "appliance": (100, 450),
    "roofing": (250, 1500),
    "carpentry": (100, 600),
    "pest control": (100, 400),
    "general maintenance": (75, 350),
}

def estimate_cost(category: str):
    key = category.lower()
    low, high = COST_RANGES.get(key, (100, 500))
    return {
        "minimum_usd": low,
        "maximum_usd": high,
        "verified": False,
        "disclaimer": "Illustrative US planning range only. Actual cost varies by location, parts, labor, diagnosis, and contractor."
    }

def find_nearby_providers(appliance_or_area: str, category: str, location: str, limit: int = 4) -> list[dict]:
    # OpenStreetMap disabled; rely on Google Maps search link below
    return []

def provider_search_links(appliance_or_area: str, category: str, location: str):
    term = appliance_or_area.strip() if appliance_or_area.strip() else category
    query = quote_plus(f"{term} repair near {location}")
    return [
        {
            "name": "Google Maps search",
            "url": f"https://www.google.com/maps/search/?api=1&query={query}",
            "note": "Live search results; verify licensing, reviews, insurance, availability, and quote directly."
        }
    ]

def find_diy_videos(appliance_or_area: str, problem_summary: str, limit: int = 3) -> dict:
    """Fetch top DIY repair YouTube tutorials with $0 API spend."""
    search_query = f"how to fix {appliance_or_area} {problem_summary}".strip()
    search_url = f"https://www.youtube.com/results?search_query={quote_plus(search_query)}"
    videos = []

    try:
        req = urllib.request.Request(
            search_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9"
            }
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            match = re.search(r"var ytInitialData = ({.*?});</script>", html)
            if match:
                data = json.loads(match.group(1))
                contents = (
                    data.get("contents", {})
                    .get("twoColumnSearchResultsRenderer", {})
                    .get("primaryContents", {})
                    .get("sectionListRenderer", {})
                    .get("contents", [])
                )
                seen_ids = set()
                for section in contents:
                    items = section.get("itemSectionRenderer", {}).get("contents", [])
                    for item in items:
                        vr = item.get("videoRenderer")
                        if not vr:
                            continue
                        vid = vr.get("videoId")
                        if not vid or vid in seen_ids:
                            continue
                        seen_ids.add(vid)
                        title = "".join(r.get("text", "") for r in vr.get("title", {}).get("runs", []))
                        channel = "".join(r.get("text", "") for r in vr.get("ownerText", {}).get("runs", []))
                        duration = vr.get("lengthText", {}).get("simpleText", "")
                        videos.append({
                            "video_id": vid,
                            "title": title,
                            "channel": channel,
                            "duration": duration,
                            "url": f"https://www.youtube.com/watch?v={vid}",
                            "thumbnail": f"https://i.ytimg.com/vi/{vid}/mqdefault.jpg"
                        })
                        if len(videos) >= limit:
                            break
                    if len(videos) >= limit:
                        break
    except Exception:
        pass

    return {
        "search_url": search_url,
        "videos": videos
    }

EMERGENCY_TERMS = [
    "gas smell", "smell of gas", "rotten egg smell",
    "smoke", "sparking", "electrical sparks", "burning smell",
    "fire", "carbon monoxide", "co alarm", "flooding near outlet"
]

def emergency_check(description: str):
    text = description.lower()
    matches = [term for term in EMERGENCY_TERMS if term in text]
    return matches