import subprocess
import json
import urllib.request
import time

edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
# Run Edge in headless mode with remote debugging port
port = 9222
proc = subprocess.Popen([
    edge,
    "--headless",
    f"--remote-debugging-port={port}",
    "http://localhost:8080"
])

time.sleep(2)

try:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/json") as r:
        pages = json.loads(r.read().decode())
        print("Pages in headless Edge:", pages)
except Exception as e:
    print("CDP Error:", e)
finally:
    proc.terminate()
