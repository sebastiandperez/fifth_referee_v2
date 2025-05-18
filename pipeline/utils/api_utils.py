import time
import requests
import re
from collections import deque

class RateLimiter:
    """Límite de solicitudes por tiempo."""
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
            print(f"Esperando {sleep_time:.2f} segundos para rate limit...")
            time.sleep(sleep_time)
        self.timestamps.append(time.time())

def extract_city(address):
    """
    Extrae la city de una dirección, que se encuentra justo antes del código postal.
    Limpia saltos de línea y espacios extra.
    Si no se encuentra, devuelve 'Desconocido'.
    """
    if not address or address == 'N/A':
        return 'Desconocido'
    # Limpiar saltos de línea y espacios
    address = address.replace('\n', ' ').strip()
    # Buscar ciudad antes de código postal (4+ dígitos)
    match = re.search(r'([a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+)\s+(\d{4,})\b', address)
    if match:
        city = match.group(1).strip()
        # Quitar espacios duplicados y normalizar
        city = re.sub(r'\s+', ' ', city)
        return city
    return 'Desconocido'