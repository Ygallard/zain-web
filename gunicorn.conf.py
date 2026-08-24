import multiprocessing
import os


bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
workers = (2 * multiprocessing.cpu_count()) + 1
timeout = 120
accesslog = "-"
errorlog = "-"
capture_output = True