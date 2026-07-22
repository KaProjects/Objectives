import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]

for path in (BACKEND_ROOT / 'test', BACKEND_ROOT / 'src', BACKEND_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
