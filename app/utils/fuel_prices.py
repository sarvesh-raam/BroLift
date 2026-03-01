"""
Real-time fuel price fetcher for Chennai, Tamil Nadu.
Scrapes live data from goodreturns.in and caches for 6 hours.
Falls back to hardcoded defaults if scraping fails.
"""
import re
import logging
import threading
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Default fallback prices (Chennai, Mar 2026)
DEFAULTS = {
    'petrol':  102.63,
    'diesel':   88.74,
    'cng':      72.00,
}

_cache = dict(DEFAULTS)
_meta = {
    'last_updated': 'Not yet fetched',
    'source': 'fallback',
    'city': 'Chennai'
}
_last_fetch_time = None
_CACHE_TTL = timedelta(hours=6)
_lock = threading.Lock()


def _scrape_price(url: str, label: str) -> float | None:
    """Scrape a fuel price from goodreturns.in. Returns float or None."""
    try:
        import requests
        from bs4 import BeautifulSoup
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/121.0.0.0 Safari/537.36'
            )
        }
        r = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(r.text, 'html.parser')

        # goodreturns shows price in <div class="price-val"> or table cells
        # Try multiple selectors to be resilient
        candidates = (
            soup.select_one('.price-val') or
            soup.select_one('.brent_rate') or
            soup.select_one('h2.petrol-price') or
            soup.select_one('strong.price')
        )
        if candidates:
            text = candidates.get_text(strip=True)
            m = re.search(r'(\d{2,3}\.\d{1,2})', text)
            if m:
                return float(m.group(1))

        # Fallback: regex scan the whole page for Rs.XX.XX pattern
        match = re.search(r'(?:₹|Rs\.?\s{0,2})(\d{2,3}\.\d{2})', r.text)
        if match:
            val = float(match.group(1))
            if 60 < val < 150:   # sanity check
                return val

    except Exception as e:
        logger.warning(f'Fuel price scrape failed ({label}): {e}')
    return None


def _do_fetch():
    """Background fetch — updates global cache in-place."""
    global _last_fetch_time, _meta
    sources = {
        'petrol': 'https://www.goodreturns.in/petrol-price-in-chennai.html',
        'diesel': 'https://www.goodreturns.in/diesel-price-in-chennai.html',
        'cng':    'https://www.goodreturns.in/cng-price-in-chennai.html',
    }
    updated = {}
    for fuel, url in sources.items():
        price = _scrape_price(url, fuel)
        if price:
            updated[fuel] = price

    with _lock:
        if updated:
            _cache.update(updated)
            _meta['source'] = 'goodreturns.in (live)'
        else:
            _meta['source'] = 'fallback (scrape failed)'
        _meta['last_updated'] = datetime.now().strftime('%d %b %Y %I:%M %p')
        _last_fetch_time = datetime.now()

    logger.info(f"Fuel prices refreshed: {_cache}  source={_meta['source']}")


def get_fuel_prices() -> dict:
    """Return current fuel prices dict, auto-refreshing every 6 hours."""
    global _last_fetch_time
    should_fetch = (
        _last_fetch_time is None or
        datetime.now() - _last_fetch_time > _CACHE_TTL
    )
    if should_fetch:
        # Fetch in background so page doesn't block
        t = threading.Thread(target=_do_fetch, daemon=True)
        t.start()
        if _last_fetch_time is None:
            t.join(timeout=6)   # Wait on very first load only

    with _lock:
        return {
            'petrol': _cache.get('petrol', DEFAULTS['petrol']),
            'diesel': _cache.get('diesel', DEFAULTS['diesel']),
            'cng':    _cache.get('cng',    DEFAULTS['cng']),
            'electric_per_km': 1.50,
            'meta': dict(_meta)
        }
