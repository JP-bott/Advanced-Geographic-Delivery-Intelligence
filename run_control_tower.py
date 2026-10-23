"""Start FastAPI and Vite together with a simple development launcher.

In Codespaces use the two-terminal commands from README for cleaner logs.
"""
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
if not (ROOT/'database/logistics_analytics.db').exists():
    print('Missing database. Run python scripts/generate_data.py && python scripts/load_database.py')
    sys.exit(1)
api=subprocess.Popen([sys.executable,'-m','uvicorn','backend.main:app','--host','0.0.0.0','--port','8000'],cwd=ROOT)
try:
    ui=subprocess.Popen(['npm','run','dev','--prefix','frontend'],cwd=ROOT)
    ui.wait()
finally:
    api.terminate()
    try:api.wait(timeout=3)
    except subprocess.TimeoutExpired:api.kill()
