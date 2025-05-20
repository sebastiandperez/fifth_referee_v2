import os
import json
import gc
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue

from getter import fetch_raw_match_json
from normalizer import clean_match_data

def process_match(url, idx, output_folder):
    try:
        raw_data = fetch_raw_match_json(url)
        if not raw_data:
            raise ValueError("Empty data")
        cleaned = clean_match_data(raw_data)
        output_path = output_folder / f"{idx}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, ensure_ascii=False, indent=4)
        return None
    except Exception as e:
        return {"url": url, "error": str(e)}

def jornada_worker(jornada_path, output_dir, max_workers=8):
    enlace_queue = Queue()
    with open(jornada_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            if url := line.strip():
                enlace_queue.put((url, idx))

    matchday = Path(jornada_path).stem
    output_folder = Path(output_dir) / matchday
    output_folder.mkdir(parents=True, exist_ok=True)
    errors = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        while not enlace_queue.empty():
            url, idx = enlace_queue.get()
            futures.append(executor.submit(process_match, url, idx, output_folder))
        for future in as_completed(futures):
            error = future.result()
            if error:
                errors.append(error)
            gc.collect()

    if errors:
        with open(output_folder / "errors.log", "w", encoding="utf-8") as f:
            json.dump(errors, f, ensure_ascii=False, indent=2)

def load_root_config():
    this_dir = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.join(this_dir, 'root.json')
    if not os.path.exists(root_path):
        raise FileNotFoundError(f"No se encontró root.json en {this_dir}")
    with open(root_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_pipeline_with_args(competition, season):
    config = load_root_config()
    max_workers = config.get("max_workers", 8)
    jornadas_dir = config["jornadas_dir"].format(competition=competition, season=season)
    output_base = config["output_base"].format(competition=competition, season=season)

    jornada_files = [Path(jornadas_dir) / f for f in sorted(os.listdir(jornadas_dir)) if f.endswith('.txt')]

    for jornada in jornada_files:
        print(f"Procesando jornada: {jornada}")
        jornada_worker(jornada, output_base, max_workers=max_workers)
        print(f"Jornada {jornada} procesada.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python worker.py <competition> <season>")
        print("Ejemplo: python worker.py bundesliga 2024_2025")
        sys.exit(1)
    competition = sys.argv[1]
    season = sys.argv[2]
    run_pipeline_with_args(competition, season)
