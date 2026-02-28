import logging
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

# Hardcoded coordinates for common Iranian cities/locations
KNOWN_LOCATIONS: dict[str, tuple[float, float]] = {
    # Iran
    "tehran": (35.6892, 51.3890),
    "isfahan": (32.6546, 51.6680),
    "tabriz": (38.0800, 46.2919),
    "shiraz": (29.5918, 52.5837),
    "mashhad": (36.2605, 59.6168),
    "ahvaz": (31.3183, 48.6706),
    "kermanshah": (34.3142, 47.0650),
    "qom": (34.6401, 50.8764),
    "karaj": (35.8400, 50.9391),
    "bushehr": (28.9234, 50.8203),
    "bandar abbas": (27.1865, 56.2808),
    "rasht": (37.2808, 49.5832),
    "kerman": (30.2839, 57.0834),
    "hamadan": (34.7990, 48.5150),
    "arak": (34.0917, 49.6892),
    "yazd": (31.8974, 54.3569),
    "ardabil": (38.2498, 48.2933),
    "sanandaj": (35.3219, 46.9862),
    "zahedan": (29.4963, 60.8629),
    "khorramabad": (33.4878, 48.3558),
    "birjand": (32.8663, 59.2211),
    "ilam": (33.6374, 46.4227),
    "gorgan": (36.8427, 54.4344),
    "sari": (36.5633, 53.0601),
    "semnan": (35.5769, 53.3975),
    "khuzestan": (31.4360, 49.0413),
    "abadan": (30.3392, 48.3043),
    "dezful": (32.3814, 48.4016),
    "khorramshahr": (30.4265, 48.1714),
    "persian gulf": (26.5000, 52.0000),
    "strait of hormuz": (26.5667, 56.2500),
    "parchin": (35.5200, 51.7700),
    "natanz": (33.5131, 51.9164),
    "fordow": (34.7089, 51.0375),
    # Israel
    "tel aviv": (32.0853, 34.7818),
    "haifa": (32.7940, 34.9896),
    "nevatim afb": (31.2083, 34.6667),
    "dimona": (31.0700, 35.2100),
    "jerusalem": (31.7683, 35.2137),
    "beer sheva": (31.2520, 34.7915),
    # Iraq (US bases)
    "al asad air base": (33.7856, 42.4411),
    "erbil": (36.1912, 44.0119),
    # Qatar
    "al udeid air base": (25.1171, 51.3150),
    # Gulf
    "gulf of oman": (25.5000, 57.0000),
}

_geocode_cache: dict[str, tuple[float, float] | None] = {}

geolocator = Nominatim(user_agent="warzone-monitor-app")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.0)


def get_coordinates(location_name: str) -> tuple[float, float] | None:
    """Convert a location name to (latitude, longitude) coordinates."""
    normalized = location_name.lower().strip()

    # Check hardcoded locations first
    if normalized in KNOWN_LOCATIONS:
        return KNOWN_LOCATIONS[normalized]

    # Check cache
    if normalized in _geocode_cache:
        return _geocode_cache[normalized]

    # Check if any known location is a substring
    for known, coords in KNOWN_LOCATIONS.items():
        if known in normalized or normalized in known:
            _geocode_cache[normalized] = coords
            return coords

    # Try geocoding via Nominatim
    try:
        result = geocode(f"{location_name}, Iran")
        if result:
            coords = (result.latitude, result.longitude)
            _geocode_cache[normalized] = coords
            return coords
    except Exception as e:
        logger.warning(f"Geocoding failed for '{location_name}': {e}")

    _geocode_cache[normalized] = None
    return None
