
"""
Utility functions for URL Pinger
"""

import re
from urllib.parse import urlparse
from typing import List


def validate_url(url: str) -> bool:
    """Validate if a string is a proper URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_urls(urls: List[str]) -> List[str]:
    """Validate a list of URLs and return only valid ones."""
    valid_urls = []
    for url in urls:
        if validate_url(url):
            valid_urls.append(url)
        else:
            print(f"Warning: '{url}' is not a valid URL and will be skipped.")
    return valid_urls


def format_duration(seconds: int) -> str:
    """Format duration in seconds to a human-readable string."""
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minutes"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours} hours, {minutes} minutes"
