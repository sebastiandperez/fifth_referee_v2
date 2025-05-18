import concurrent.futures
from batch.batch_json import BatchExtractor

class MultiBatchExtractor:
    def __init__(self, queue_matchdays, max_workers=4):
        """
        queue_matchdays: Queue principal (de jornadas)
        max_workers: número de hilos en paralelo
        """
        self.queue_matchdays = queue_matchdays
        self.max_workers = max_workers

    def process_all_matchdays(self):
        """
        Procesa todas las jornadas en paralelo usando BatchExtractor.
        Retorna una lista con los resultados de cada jornada (dicts).
        """
        results = []

        def process_jornada_worker(match_queue):
            batch_extractor = BatchExtractor(match_queue)
            return batch_extractor.process_all_files()

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            while not self.queue_matchdays.empty():
                match_queue = self.queue_matchdays.get()
                future = executor.submit(process_jornada_worker, match_queue)
                futures.append(future)

            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)

        return results
