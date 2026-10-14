"""Step 4: retrieve the top chunks for a question from one agent's collection."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import get_embeddings  # noqa: E402
from src.retrieval import AGENT_COLLECTION, describe_source  # noqa: E402
from src.vectorstore import load_existing  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument("question")
parser.add_argument("--agent", default="HIOT_agent", choices=list(AGENT_COLLECTION))
parser.add_argument("--k", type=int, default=5)
args = parser.parse_args()

dbs = load_existing(get_embeddings())
db = dbs[AGENT_COLLECTION[args.agent]]
hits = db.similarity_search_with_score(args.question, k=args.k)

print(f"agent: {args.agent}   collection: {AGENT_COLLECTION[args.agent]}   k: {args.k}")
print("(distance: lower = closer match)\n")
for i, (doc, score) in enumerate(hits, start=1):
    preview = doc.page_content.replace("\n", " ")[:200]
    print(f"{i}. distance {score:.4f} | {describe_source(doc)}")
    print(f"   {preview} ...\n")
