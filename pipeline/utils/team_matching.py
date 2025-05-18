from rapidfuzz import fuzz
import pandas as pd

def match_teams_progressive(df1, df2, col1, col2,
                            strict_threshold=90,
                            flexible_threshold=80,
                            final_threshold=70):
    """
    Matches team names progressively using three strategies:
    1. Strict token_sort_ratio
    2. Flexible partial_ratio
    3. Weighted combo of token_sort, token_set, partial

    Returns:
        DataFrame with matches and similarity metadata
        Columns: team_name_scraped, team_name_api, similitud, metodo
    """
    matched = {}
    remaining = set(df1[col1])
    candidates = df2[col2].tolist()

    def best_match(nombre1, scorer, threshold):
        best_score = 0
        best_name = None
        for nombre2 in candidates:
            score = scorer(nombre1, nombre2)
            if score > best_score:
                best_score = score
                best_name = nombre2
        if best_score >= threshold:
            return best_name, best_score
        return None, None

    # Primera ronda: token_sort_ratio estricto
    for name in list(remaining):
        match, score = best_match(name, fuzz.token_sort_ratio, strict_threshold)
        if match:
            matched[name] = (match, score, "token_sort_ratio")
            remaining.remove(name)

    # Segunda ronda: partial_ratio
    for name in list(remaining):
        match, score = best_match(name, fuzz.partial_ratio, flexible_threshold)
        if match:
            matched[name] = (match, score, "partial_ratio")
            remaining.remove(name)

    # Tercera ronda: combinación ponderada
    for name in list(remaining):
        best_score = 0
        best_match_name = None
        for other in candidates:
            ts = fuzz.token_sort_ratio(name, other)
            tset = fuzz.token_set_ratio(name, other)
            part = fuzz.partial_ratio(name, other)
            final_score = 0.4 * ts + 0.3 * tset + 0.3 * part
            if final_score > best_score:
                best_score = final_score
                best_match_name = other
        if best_score >= final_threshold:
            matched[name] = (best_match_name, best_score, "combo_weighted")
            remaining.remove(name)

    # Construir el DataFrame final con los nombres correctos
    resultados = []
    for name in df1[col1]:
        if name in matched:
            match, score, method = matched[name]
            resultados.append({
                'team_name_scraped': name,  # Nombre en tu DataFrame principal
                'team_name_api': match,     # Nombre en el DataFrame API
                'similitud': round(score, 2),
                'metodo': method
            })
        else:
            resultados.append({
                'team_name_scraped': name,
                'team_name_api': None,
                'similitud': None,
                'metodo': "no_match"
            })

    return pd.DataFrame(resultados)
