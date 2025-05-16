import psutil
from functools import wraps
import time

def measure_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"⏱  {func.__name__} tardó {(end - start):.2f} segundos.")
        return result
    return wrapper

def monitor_memory(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        ram_before = psutil.Process().memory_info().rss / (1024 ** 2)
        result = func(*args, **kwargs)
        gc.collect()
        ram_after = psutil.Process().memory_info().rss / (1024 ** 2)
        print(f"📈 {func.__name__}: RAM antes={ram_before:.2f}MB, después={ram_after:.2f}MB, delta={ram_after - ram_before:.2f}MB")
        return result
    return wrapper
