"""Embedding and storage: four persistent Chroma collections."""
from pathlib import Path

from langchain_chroma import Chroma

from src.paths import CHROMA_ROOT

COLLECTIONS = ["finance_reporting", "hr_policy", "supply_chain", "healthcare_iot"]


def _open(collection_name, embeddings, chroma_root=None) -> Chroma:
    root = Path(chroma_root) if chroma_root else CHROMA_ROOT
    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=str(root / collection_name),
    )


def _count(store: Chroma) -> int:
    return store._collection.count()


def build_or_load_chroma(documents, collection_name, embeddings, chroma_root=None, rebuild=False) -> Chroma:
    store = _open(collection_name, embeddings, chroma_root)
    if rebuild:
        # Use Chroma's own API; deleting the folder fails on Windows while files are open.
        store.delete_collection()
        store = _open(collection_name, embeddings, chroma_root)
    if _count(store) > 0:
        print(f"Loaded  {collection_name} ({_count(store)} chunks)")
        return store
    store.add_documents(documents)
    print(f"Created {collection_name} ({_count(store)} chunks)")
    return store


def build_all(corpora, embeddings, chroma_root=None, rebuild=False) -> dict:
    return {
        name: build_or_load_chroma(corpora[name], name, embeddings, chroma_root, rebuild)
        for name in COLLECTIONS
    }


def load_existing(embeddings, chroma_root=None) -> dict:
    stores = {name: _open(name, embeddings, chroma_root) for name in COLLECTIONS}
    empty = [name for name, store in stores.items() if _count(store) == 0]
    if empty:
        raise RuntimeError(
            "Empty or missing collection(s): " + ", ".join(empty)
            + ". Run scripts/step3_embed_store.py first."
        )
    return stores
