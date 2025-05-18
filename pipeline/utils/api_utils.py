import time
import requests
import re
from collections import deque

class RateLimiter:
    """Time limite for API Requests."""
    def __init__(self, max_requests=5, period=60):
        self.max_requests = max_requests
        self.period = period
        self.timestamps = deque()
    
    def wait(self):
        current_time = time.time()
        while self.timestamps and current_time - self.timestamps[0] > self.period:
            self.timestamps.popleft()
        if len(self.timestamps) >= self.max_requests:
            sleep_time = self.period - (current_time - self.timestamps[0])
            print(f"Waiting {sleep_time:.2f} seconds for rate limit...")
            time.sleep(sleep_time)
        self.timestamps.append(time.time())

def extract_city(address):
    """
    Extracts the city from an address, which is located just before the postal code.
    Removes line breaks and extra spaces.
    If not found, returns 'Unknown'.
    """
    if not address or address == 'N/A':
        return 'Unknown'
    address = address.replace('\n', ' ').strip()
    match = re.search(r'([a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+)\s+(\d{4,})\b', address)
    if match:
        city = match.group(1).strip()
        city = re.sub(r'\s+', ' ', city)
        parts = city.split(" ", 1)
        if len(parts) == 2 and len(parts[0]) < 2:
            city = parts[1]
        return city
    return 'Unknown'