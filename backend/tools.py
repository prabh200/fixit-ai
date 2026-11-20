# # from urllib.parse import quote_plus

# # # These are broad planning ranges only. They are not sourced local quotes.
# # COST_RANGES = {
# #     "plumbing": (100, 450),
# #     "electrical": (120, 500),
# #     "hvac": (150, 900),
# #     "appliance": (100, 450),
# #     "roofing": (250, 1500),
# #     "carpentry": (100, 600),
# #     "pest control": (100, 400),
# #     "general maintenance": (75, 350),
# # }

# # def estimate_cost(category: str):
# #     key = category.lower()
# #     low, high = COST_RANGES.get(key, (100, 500))
# #     return {
# #         "minimum_usd": low,
# #         "maximum_usd": high,
# #         "verified": False,
# #         "disclaimer": "Illustrative US planning range only. Actual cost varies by location, parts, labor, diagnosis, and contractor."
# #     }

# # def provider_search_links(category: str, location: str):
# #     query = quote_plus(f"{category} repair service near {location}")
# #     return [
# #         {
# #             "name": "Google Maps search",
# #             "url": f"https://www.google.com/maps/search/{query}",
# #             "note": "Live search results; verify licensing, reviews, insurance, availability, and quote directly."
# #         },
# #         {
# #             "name": "OpenStreetMap search",
# #             "url": f"https://www.openstreetmap.org/search?query={query}",
# #             "note": "Map search; provider details and coverage may vary."
# #         }
# #     ]

# # EMERGENCY_TERMS = [
# #     "gas smell", "smell of gas", "rotten egg smell",
# #     "smoke", "sparking", "electrical sparks", "burning smell",
# #     "fire", "carbon monoxide", "co alarm", "flooding near outlet"
# # ]

# # def emergency_check(description: str):
# #     text = description.lower()
# #     matches = [term for term in EMERGENCY_TERMS if term in text]
# #     return matches




# import re
# import json
# import urllib.request
# from urllib.parse import quote_plus

# COST_RANGES = {
#     "plumbing": (100, 450),
#     "electrical": (120, 500),
#     "hvac": (150, 900),
#     "appliance": (100, 450),
#     "roofing": (250, 1500),
#     "carpentry": (100, 600),
#     "pest control": (100, 400),
#     "general maintenance": (75, 350),
# }

# def estimate_cost(category: str):
#     key = category.lower()
#     low, high = COST_RANGES.get(key, (100, 500))
#     return {
#         "minimum_usd": low,
#         "maximum_usd": high,
#         "verified": False,
#         "disclaimer": "Illustrative US planning range only. Actual cost varies by location, parts, labor, diagnosis, and contractor."
#     }

# def _geocode_location(location: str):
#     """Convert a ZIP code or city into (lat, lon) using Nominatim."""
#     if not location or not location.strip():
#         return None
#     url = f"https://nominatim.openstreetmap.org/search?q={quote_plus(location.strip())}&format=json&limit=1"
#     req = urllib.request.Request(url, headers={"User-Agent": "FixItAI-Hackathon/1.0"})
#     try:
#         with urllib.request.urlopen(req, timeout=5) as resp:
#             data = json.loads(resp.read().decode("utf-8"))
#             if data:
#                 return float(data[0]["lat"]), float(data[0]["lon"])
#     except Exception:
#         pass
#     return None

# def find_nearby_providers(appliance_or_area: str, category: str, location: str, limit: int = 4) -> list[dict]:
#     """Find real nearby repair shops via OpenStreetMap Overpass API around the user's location."""
#     coords = _geocode_location(location)
#     if not coords:
#         return []

#     lat, lon = coords
#     overpass_query = f"""
#     [out:json][timeout:8];
#     (
#       node["shop"~"repair|electronics|computer|hardware|mobile_phone"](around:12000,{lat},{lon});
#       way["shop"~"repair|electronics|computer|hardware|mobile_phone"](around:12000,{lat},{lon});
#       node["craft"~"plumber|electrician|hvac|carpenter|roofer"](around:12000,{lat},{lon});
#     );
#     out center 15;
#     """
#     try:
#         req = urllib.request.Request(
#             "https://overpass-api.de/api/interpreter",
#             data=overpass_query.encode("utf-8"),
#             headers={"User-Agent": "FixItAI-Hackathon/1.0"}
#         )
#         with urllib.request.urlopen(req, timeout=8) as resp:
#             data = json.loads(resp.read().decode("utf-8"))
#             results = []
#             seen = set()
#             for el in data.get("elements", []):
#                 tags = el.get("tags", {})
#                 name = tags.get("name")
#                 if not name or name in seen:
#                     continue
#                 seen.add(name)

#                 el_lat = el.get("lat") or el.get("center", {}).get("lat", lat)
#                 el_lon = el.get("lon") or el.get("center", {}).get("lon", lon)
#                 street = f"{tags.get('addr:housenumber', '')} {tags.get('addr:street', '')}".strip()
#                 city = tags.get("addr:city", location)
#                 address = f"{street}, {city}".strip(", ") if street else f"Near {city}"

#                 results.append({
#                     "name": name,
#                     "address": address,
#                     "map_url": f"https://www.openstreetmap.org/?mlat={el_lat}&mlon={el_lon}#map=16/{el_lat}/{el_lon}",
#                     "google_maps_url": f"https://www.google.com/maps/search/{quote_plus(f'{name} {address}')}"
#                 })
#                 if len(results) >= limit:
#                     break
#             return results
#     except Exception:
#         return []

# def provider_search_links(appliance_or_area: str, category: str, location: str):
#     term = appliance_or_area.strip() if appliance_or_area.strip() else category
#     query = quote_plus(f"{term} repair near {location}")
#     coords = _geocode_location(location)
#     osm_url = (
#         f"https://www.openstreetmap.org/?mlat={coords[0]}&mlon={coords[1]}#map=13/{coords[0]}/{coords[1]}"
#         if coords else f"https://www.openstreetmap.org/search?query={quote_plus(location)}"
#     )
#     return [
#         {
#             "name": "Google Maps search",
#             "url": f"https://www.google.com/maps/search/{query}",
#             "note": "Live search results; verify licensing, reviews, insurance, availability, and quote directly."
#         },
#         {
#             "name": "OpenStreetMap area view",
#             "url": osm_url,
#             "note": f"Centered on {location}; shows local map area."
#         }
#     ]

# def find_diy_videos(appliance_or_area: str, problem_summary: str, limit: int = 3) -> dict:
#     """Fetch top DIY repair YouTube tutorials with $0 API spend."""
#     search_query = f"how to fix {appliance_or_area} {problem_summary}".strip()
#     search_url = f"https://www.youtube.com/results?search_query={quote_plus(search_query)}"
#     videos = []

#     try:
#         req = urllib.request.Request(
#             search_url,
#             headers={
#                 "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
#                 "Accept-Language": "en-US,en;q=0.9"
#             }
#         )
#         with urllib.request.urlopen(req, timeout=6) as resp:
#             html = resp.read().decode("utf-8", errors="ignore")
#             match = re.search(r"var ytInitialData = ({.*?});</script>", html)
#             if match:
#                 data = json.loads(match.group(1))
#                 contents = (
#                     data.get("contents", {})
#                     .get("twoColumnSearchResultsRenderer", {})
#                     .get("primaryContents", {})
#                     .get("sectionListRenderer", {})
#                     .get("contents", [])
#                 )
#                 seen_ids = set()
#                 for section in contents:
#                     items = section.get("itemSectionRenderer", {}).get("contents", [])
#                     for item in items:
#                         vr = item.get("videoRenderer")
#                         if not vr:
#                             continue
#                         vid = vr.get("videoId")
#                         if not vid or vid in seen_ids:
#                             continue
#                         seen_ids.add(vid)
#                         title = "".join(r.get("text", "") for r in vr.get("title", {}).get("runs", []))
#                         channel = "".join(r.get("text", "") for r in vr.get("ownerText", {}).get("runs", []))
#                         duration = vr.get("lengthText", {}).get("simpleText", "")
#                         videos.append({
#                             "video_id": vid,
#                             "title": title,
#                             "channel": channel,
#                             "duration": duration,
#                             "url": f"https://www.youtube.com/watch?v={vid}",
#                             "thumbnail": f"https://i.ytimg.com/vi/{vid}/mqdefault.jpg"
#                         })
#                         if len(videos) >= limit:
#                             break
#                     if len(videos) >= limit:
#                         break
#     except Exception:
#         pass

#     return {
#         "search_url": search_url,
#         "videos": videos
#     }

# EMERGENCY_TERMS = [
#     "gas smell", "smell of gas", "rotten egg smell",
#     "smoke", "sparking", "electrical sparks", "burning smell",
#     "fire", "carbon monoxide", "co alarm", "flooding near outlet"
# ]

# def emergency_check(description: str):
#     text = description.lower()
#     matches = [term for term in EMERGENCY_TERMS if term in text]
#     return matches



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