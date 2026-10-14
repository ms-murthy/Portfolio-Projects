"""Print which environment variables are set. Never prints values."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import OPTIONAL_KEYS, REQUIRED_KEYS, check_env  # noqa: E402

status = check_env()

for key in REQUIRED_KEYS:
    print(f"{key:<22} {'set' if status[key] else 'MISSING'}")
for key in OPTIONAL_KEYS:
    print(f"{key:<22} {'set' if status[key] else 'not set (optional)'}")

ready = all(status[key] for key in REQUIRED_KEYS)
print("READY" if ready else "NOT READY")
sys.exit(0 if ready else 1)
