import multiprocessing
import os


bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
calculated_workers = (2 * multiprocessing.cpu_count()) + 1
max_workers = int(os.getenv("GUNICORN_MAX_WORKERS", "2"))
workers = min(calculated_workers, max_workers)
timeout = 120
accesslog = "-"
errorlog = "-"
capture_output = True