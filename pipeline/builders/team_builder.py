from utils.api_utils import RateLimiter, extract_city
from utils.team_matching import match_teams_progressive
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def build_team_dataframe_from_matches(all_matches):
    """
    Builds a DataFrame containing unique teams extracted from the match data.

    This function processes a list of match dictionaries, each containing information 
    about local and away teams. It extracts the team_id and team_name for both teams 
    from every match, then deduplicates them to ensure each team appears only once.

    Args:
        all_matches (list of dict): List of match records, each with keys such as 
            'local_team_id', 'local_team_name', 'away_team_id', 'away_team_name'.

    Returns:
        pd.DataFrame: DataFrame with columns ['team_id', 'team_name'], one row per unique team.
    """
    teams_list = []
    for match in all_matches:
        teams_list.append({
            "team_id": match["local_team_id"],
            "team_name": match["local_team_name"]
        })
        teams_list.append({
            "team_id": match["away_team_id"],
            "team_name": match["away_team_name"]
        })
    df_teams = pd.DataFrame(teams_list).drop_duplicates(subset=["team_id", "team_name"]).reset_index(drop=True)
    return df_teams

def build_teams_from_footdata_API(nombre_liga, token, max_requests=5, period=60, max_workers=5):
    """
    Fetches and builds a DataFrame of teams in a given league using the football-data.org API.

    This function retrieves the list of teams for a specific league, 
    collects additional information (such as city and stadium) for each team, 
    and returns a cleaned DataFrame ready for downstream processing or matching.

    Args:
        league_name (str): Name of the league to query.
        token (str): API authentication token.
        max_requests (int): Max requests allowed per time period.
        period (int): Time period (in seconds) for rate limiting.
        max_workers (int): Number of parallel workers for data fetching.

    Returns:
        pd.DataFrame: DataFrame with columns such as ['team', 'city', 'stadium'].
    """
    headers = {"X-Auth-Token": token}
    rate_limiter = RateLimiter(max_requests=max_requests, period=period)

    print("ID League...")
    rate_limiter.wait()
    response = requests.get("https://api.football-data.org/v4/competitions/", headers=headers)
    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}")
    
    if nombre_liga.lower() in ["la_liga", "la liga"]:
        nombre_liga = "primera division"
    competiciones = response.json()
    id_competicion = next(
        (c['id'] for c in competiciones['competitions']
         if c['name'].lower() == nombre_liga.lower()), 
        None
    )
    if not id_competicion:
        raise Exception(f"League '{nombre_liga}' not found in football-data.org")

    # 2. Obtener IDs de equipos de la liga
    print("Team IDs...")
    rate_limiter.wait()
    url_equipos = f"https://api.football-data.org/v4/competitions/{id_competicion}/teams"
    response = requests.get(url_equipos, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}")
    ids_equipos = [team['id'] for team in response.json()['teams']]

    def get_team_info(team_id):
        rate_limiter.wait()
        url_team = f"https://api.football-data.org/v4/teams/{team_id}"
        try:
            response = requests.get(url_team, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return {
                    'team_name': data.get('name'),
                    'city': extract_city(data.get('address', 'N/A')),
                    'stadium': data.get('venue', 'N/A')
                }
            else:
                print(f"Error team_id: {team_id}: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error team_id: {team_id}: {e}")
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

def build_team_dataframe(all_matches, league_name, token):
    """
    Builds and enriches the teams DataFrame with city and stadium information from the API.

    Args:
        all_matches (list): List of match dictionaries (raw data from matches).
        league_name (str): Name of the league for external API enrichment.
        token (str): API authentication token.

    Returns:
        pd.DataFrame: DataFrame with columns ['team_id', 'team_name', 'city', 'stadium'].
    """
    main_dataframe = build_team_dataframe_from_matches(all_matches)    
    secondary_dataframe = build_teams_from_footdata_API(league_name, token)
    
    # Matching
    matches = match_teams_progressive(main_dataframe, secondary_dataframe, "team_name", "team_name")
    
    # Map API team names to local team names
    api_to_local_mapping = dict(zip(matches['team_name_api'], matches['team_name_scraped']))
    secondary_dataframe['team_name'] = secondary_dataframe['team_name'].replace(api_to_local_mapping)

    # Final merge
    df_teams = pd.merge(
        main_dataframe,
        secondary_dataframe[['team_name', 'city', 'stadium']],
        on="team_name",
        how="left"
    )

    print(df_teams)
    return df_teams
