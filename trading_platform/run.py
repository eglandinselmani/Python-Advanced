"""Start the FastAPI backend (port 8000) and the Streamlit frontend (port 8501) together.

    python run.py
Press Ctrl+C to stop both.
"""
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
HOST = os.getenv("BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = os.getenv("BACKEND_PORT", "8000")
FRONTEND_PORT = os.getenv("FRONTEND_PORT", "8501")


def wait_for(url: str, timeout: float = 40) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception:
            time.sleep(0.5)
    return False


def main() -> int:
    env = {**os.environ, "API_URL": f"http://{HOST}:{BACKEND_PORT}", "PYTHONPATH": str(ROOT)}
    backend = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.main:app", "--host", HOST, "--port", BACKEND_PORT],
                               cwd=ROOT, env=env)
    if not wait_for(f"http://{HOST}:{BACKEND_PORT}/api/health"):
        print("Backend failed to start.")
        backend.terminate()
        return 1
    frontend = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "frontend/app.py", "--server.port", FRONTEND_PORT,
                                 "--server.headless", "true"], cwd=ROOT, env=env)
    print(f"\n  Frontend : http://localhost:{FRONTEND_PORT}\n  Backend  : http://localhost:{BACKEND_PORT}\n"
          f"  API docs : http://localhost:{BACKEND_PORT}/docs\n  (Ctrl+C to stop)\n")
    try:
        while backend.poll() is None and frontend.poll() is None:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        for p in (frontend, backend):
            if p.poll() is None:
                p.terminate()
        for p in (frontend, backend):
            try:
                p.wait(timeout=8)
            except subprocess.TimeoutExpired:
                p.kill()
    return 0


if __name__ == "__main__":
    sys.exit(main())
