import time
import requests
import re
import pandas as pd
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from rapidfuzz import process, fuzz

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

def extraer_ciudad(direccion):
    """
    Extrae la ciudad de una dirección, que se encuentra justo antes del código postal.
    Limpia saltos de línea y espacios extra.
    Si no se encuentra, devuelve 'Desconocido'.
    """
    if not direccion or direccion == 'N/A':
        return 'Desconocido'
    # Limpiar saltos de línea y espacios
    direccion = direccion.replace('\n', ' ').strip()
    # Buscar ciudad antes de código postal (4+ dígitos)
    match = re.search(r'([a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+)\s+(\d{4,})\b', direccion)
    if match:
        ciudad = match.group(1).strip()
        # Quitar espacios duplicados y normalizar
        ciudad = re.sub(r'\s+', ' ', ciudad)
        return ciudad
    return 'Desconocido'

def get_teams_footdata(nombre_liga, token, max_requests=5, period=60, max_workers=5):
    """
    Extrae un DataFrame con info de equipos de una liga usando football-data.org.
    Devuelve un DataFrame con 'team', 'city', 'stadium'.
    """
    # Configuración de headers y rate limiter
    headers = {"X-Auth-Token": token}
    rate_limiter = RateLimiter(max_requests=max_requests, period=period)

    # 1. Obtener ID de la liga
    print("Obteniendo ID de la liga...")
    rate_limiter.wait()
    response = requests.get("https://api.football-data.org/v4/competitions/", headers=headers)
    if response.status_code != 200:
        raise Exception(f"Error al obtener competiciones: {response.status_code}")
    
    if nombre_liga.lower() in ["la_liga", "la liga"]:
        nombre_liga = "primera division"
    competiciones = response.json()
    id_competicion = next(
        (c['id'] for c in competiciones['competitions']
         if c['name'].lower() == nombre_liga.lower()), 
        None
    )
    if not id_competicion:
        raise Exception(f"Liga '{nombre_liga}' no encontrada en football-data.org")

    # 2. Obtener IDs de equipos de la liga
    print("Obteniendo IDs de equipos...")
    rate_limiter.wait()
    url_equipos = f"https://api.football-data.org/v4/competitions/{id_competicion}/teams"
    response = requests.get(url_equipos, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Error al obtener equipos: {response.status_code}")
    ids_equipos = [team['id'] for team in response.json()['teams']]

    # 3. Scraping paralelo de info de cada equipo
    def get_team_info(team_id):
        rate_limiter.wait()
        url_team = f"https://api.football-data.org/v4/teams/{team_id}"
        try:
            response = requests.get(url_team, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return {
                    'team': data.get('name'),
                    'city': extraer_ciudad(data.get('address', 'N/A')),
                    'stadium': data.get('venue', 'N/A')
                }
            else:
                print(f"Error al obtener info equipo {team_id}: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error al obtener info equipo {team_id}: {e}")
            return None

    print("Obteniendo información de los equipos (puede demorar)...")
    resultados = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futuros = [executor.submit(get_team_info, tid) for tid in ids_equipos]
        for futuro in as_completed(futuros):
            res = futuro.result()
            if res:
                resultados.append(res)

    print("Generando DataFrame final...")
    df = pd.DataFrame(resultados)
    return df
