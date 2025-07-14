
#!/usr/bin/env python3
"""
URL Pinger - A simple tool to ping multiple URLs at regular intervals
Author: jashgro (https://bit.ly/jashgro)
Updates: https://github.com/BlackHatDevX/Render-Pinger
"""

import requests
import time
import sys
from typing import List
from config import REQUEST_TIMEOUT, USER_AGENT
from utils import validate_urls, format_duration


class URLPinger:
    """A class to handle URL pinging functionality."""
    
    def __init__(self, urls: List[str], interval: int):
        self.urls = urls
        self.interval = interval
    
    def ping_url(self, url: str, retries: int = 2) -> bool:
        """Send a GET request to a URL and return success status."""
        headers = {'User-Agent': USER_AGENT}
        
        for attempt in range(retries + 1):
            try:
                response = requests.get(url, timeout=REQUEST_TIMEOUT, headers=headers)
                if response.status_code == 200:
                    response_time = response.elapsed.total_seconds()
                    print(f"✓ Pinged {url} at {time.strftime('%H:%M:%S')} (Response time: {response_time:.2f}s)")
                    return True
                else:
                    print(f"✗ Failed to ping {url}. Status code: {response.status_code}")
                    return False
            except requests.exceptions.Timeout:
                if attempt < retries:
                    print(f"⚠ Timeout for {url}, retrying... (attempt {attempt + 1}/{retries + 1})")
                    time.sleep(2)  # Brief pause before retry
                else:
                    print(f"✗ Timeout error for {url} after {retries + 1} attempts (timeout: {REQUEST_TIMEOUT}s)")
            except requests.RequestException as e:
                if attempt < retries:
                    print(f"⚠ Error pinging {url}: {e}, retrying... (attempt {attempt + 1}/{retries + 1})")
                    time.sleep(2)
                else:
                    print(f"✗ Error pinging {url}: {e}")
        
        return False
    
    def ping_all_urls(self) -> None:
        """Ping all URLs in the list."""
        for url in self.urls:
            self.ping_url(url)
    
    def start_pinging(self) -> None:
        """Start the continuous pinging process."""
        print(f"Starting URL pinger with {len(self.urls)} URLs")
        print(f"Interval: {format_duration(self.interval)}")
        print(f"Timeout: {REQUEST_TIMEOUT}s per request")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                print(f"--- Ping cycle at {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
                self.ping_all_urls()
                print(f"Waiting {format_duration(self.interval)}...\n")
                time.sleep(self.interval)
        except KeyboardInterrupt:
            print("\nPinging stopped by user.")
            sys.exit(0)


def get_urls_from_user() -> List[str]:
    """Get URLs from user input."""
    option = input("Do you want to enter multiple URLs? (yes/no): ").lower()
    
    if option == "yes":
        urls_input = input("Enter the URLs separated by space: ")
        urls = urls_input.split()
    else:
        url = input("Enter the URL: ")
        urls = [url]
    
    # Validate URLs using utility function
    return validate_urls(urls)


def get_interval_from_user() -> int:
    """Get time interval from user input."""
    while True:
        try:
            interval = int(input("Enter the time interval between requests (in seconds): "))
            if interval > 0:
                return interval
            else:
                print("Please enter a positive number.")
        except ValueError:
            print("Please enter a valid number.")


def main():
    """Main function to run the URL pinger."""
    print("URL Pinger Tool")
    print("Script made by jashgro (https://bit.ly/jashgro)")
    print("Updates on https://github.com/BlackHatDevX/Render-Pinger\n")
    
    # Get URLs and interval from user
    urls = get_urls_from_user()
    if not urls:
        print("No valid URLs provided. Exiting.")
        sys.exit(1)
    
    interval = get_interval_from_user()
    
    # Create and start the pinger
    pinger = URLPinger(urls, interval)
    pinger.start_pinging()


if __name__ == "__main__":
    main()
