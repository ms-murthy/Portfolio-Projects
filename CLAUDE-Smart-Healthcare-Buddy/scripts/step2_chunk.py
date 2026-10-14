"""Step 2: chunk the PDF and check the chunks."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingest import chunk_documents, load_pdf_pages  # noqa: E402

pages = load_pdf_pages()
chunks = chunk_documents(pages)
lengths = [len(c.page_content) for c in chunks]

print(f"pages: {len(pages)}  ->  chunks: {len(chunks)}")
print(f"chunk length  min: {min(lengths)}  avg: {sum(lengths) // len(lengths)}  max: {max(lengths)}")

with_page = [c for c in chunks if isinstance(c.metadata.get("page"), int) and c.metadata["page"] >= 1]
print(f"chunks with a page number: {len(with_page)} of {len(chunks)}",
      "(all OK)" if len(with_page) == len(chunks) else "(PROBLEM)")
print(f"page range: {min(c.metadata['page'] for c in with_page)} to {max(c.metadata['page'] for c in with_page)}")

sample = chunks[10]
print("sample metadata:", {k: sample.metadata[k] for k in ("department", "source", "page")})
print("sample text    :", sample.page_content[:300].replace("\n", " | "), "...")
