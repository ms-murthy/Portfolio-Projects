"""Step 3: embed the corpora and store them in four Chroma collections."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import check_env, get_embeddings  # noqa: E402
from src.ingest import load_all_corpora  # noqa: E402
from src.vectorstore import COLLECTIONS, build_all  # noqa: E402

rebuild = "--rebuild" in sys.argv

status = check_env()
missing = [k for k in ("OPENAI_API_KEY", "EMBEDDING_MODEL_NAME") if not status[k]]
if missing:
    sys.exit("Missing: " + ", ".join(missing))

corpora = load_all_corpora()
expected = {name: len(corpora[name]) for name in COLLECTIONS}

stores = build_all(corpora, get_embeddings(), rebuild=rebuild)

print("\ncollection           stored  expected")
all_ok = True
for name in COLLECTIONS:
    stored = stores[name]._collection.count()
    ok = stored == expected[name]
    all_ok &= ok
    print(f"{name:<20} {stored:>6}  {expected[name]:>8}  {'OK' if ok else 'MISMATCH'}")
print("ALL OK" if all_ok else "PROBLEM")
