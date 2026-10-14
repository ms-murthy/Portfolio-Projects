"""Reading and chunking: turn the four sources into LangChain Documents."""
import json
from pathlib import Path

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.paths import FINANCE_FILE, HIOT_FILE, HR_FILE, SUPPLY_CHAIN_FILE

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200


def json_to_documents(path, department: str) -> list[Document]:
    """One Document per record in a JSON list."""
    path = Path(path)
    with open(path, encoding="utf-8") as f:
        records = json.load(f)
    return [
        Document(
            page_content=f"Department: {department}\nTopic: {r['topic']}\n\n{r['content']}",
            metadata={
                "department": department,
                "topic": r["topic"],
                "source": path.name,
                "record_id": i,
            },
        )
        for i, r in enumerate(records)
    ]


def load_json_corpora() -> dict[str, list[Document]]:
    return {
        "finance_reporting": json_to_documents(FINANCE_FILE, "finance_reporting"),
        "hr_policy": json_to_documents(HR_FILE, "hr_policy"),
        "supply_chain": json_to_documents(SUPPLY_CHAIN_FILE, "supply_chain"),
    }


def load_pdf_pages() -> list[Document]:
    """One Document per PDF page, with page numbers starting at 1."""
    pages = PyMuPDFLoader(str(HIOT_FILE)).load()
    for doc in pages:
        doc.metadata["department"] = "healthcare_iot"
        doc.metadata["source"] = HIOT_FILE.name
        doc.metadata["page"] = int(doc.metadata.get("page", 0)) + 1
    return pages


def chunk_documents(docs: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(docs)


def load_all_corpora() -> dict[str, list[Document]]:
    corpora = load_json_corpora()
    corpora["healthcare_iot"] = chunk_documents(load_pdf_pages())
    return corpora
