import os
import queue

def build_matchday_queues(json_data_root, competition_name, season_label):
    """
    Devuelve un Queue principal de jornadas, donde cada elemento es un Queue con los partidos (.json) de esa jornada.
    """
    matchdays_root = os.path.join(json_data_root, competition_name, season_label, "match_data")
    if not os.path.exists(matchdays_root):
        raise FileNotFoundError(f"match_data directory not found: {matchdays_root}")

    queue_matchdays = queue.Queue()
    matchday_dirs = [
        os.path.join(matchdays_root, d)
        for d in os.listdir(matchdays_root)
        if os.path.isdir(os.path.join(matchdays_root, d)) and d.isdigit()
    ]
    matchday_dirs.sort(key=lambda path: int(os.path.basename(path)))
    for matchday_dir in matchday_dirs:
        q_matches = build_match_queue_from_dir(matchday_dir)
        if not q_matches.empty():
            queue_matchdays.put(q_matches)
    return queue_matchdays

def build_match_queue_from_dir(matchday_dir):
    """
    Dada una carpeta de jornada, devuelve una Queue con los paths a archivos .json ordenados numéricamente.
    """
    q = queue.Queue()
    match_files = [
        f for f in os.listdir(matchday_dir)
        if f.endswith('.json') and f.split('.')[0].isdigit()
    ]
    for file in sorted(match_files, key=lambda x: int(x.split('.')[0])):
        q.put(os.path.join(matchday_dir, file))
    return q

