
"""One place for every path in the project."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "Data"
CHROMA_ROOT = PROJECT_ROOT / "chroma_db"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
ENV_PATH = PROJECT_ROOT / ".env"

FINANCE_FILE = DATA_DIR / "finance_reporting_agent.json"
HR_FILE = DATA_DIR / "hr_policy_agent.json"
SUPPLY_CHAIN_FILE = DATA_DIR / "supply_chain_agent.json"
HIOT_FILE = DATA_DIR / "Trends, prospects, challenges, and security in HIOT.pdf"
