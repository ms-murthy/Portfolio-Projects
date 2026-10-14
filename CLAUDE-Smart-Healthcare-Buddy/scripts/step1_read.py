"""Step 1: read the four sources and show how much each produced."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingest import load_json_corpora, load_pdf_pages  # noqa: E402


def show_sample(doc):
    print("  metadata:", doc.metadata)
    print("  text    :", doc.page_content[:300].replace("\n", " | "), "...")


corpora = load_json_corpora()
for name, docs in corpora.items():
    print(f"{name}: {len(docs)} records")
    show_sample(docs[0])

pages = load_pdf_pages()
print(f"healthcare_iot: {len(pages)} pages")
show_sample(pages[0])
