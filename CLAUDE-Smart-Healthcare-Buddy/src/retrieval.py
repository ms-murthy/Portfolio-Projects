"""Retrieval: top-k chunks per agent, each labelled with its source."""
AGENT_COLLECTION = {
    "finance_agent": "finance_reporting",
    "hr_agent": "hr_policy",
    "supply_chain_agent": "supply_chain",
    "HIOT_agent": "healthcare_iot",
}


def make_retriever(vector_db, k: int = 5):
    return vector_db.as_retriever(search_type="similarity", search_kwargs={"k": k})


def describe_source(doc) -> str:
    source = doc.metadata.get("source", "unknown")
    if "page" in doc.metadata:
        return f"{source}, page {doc.metadata['page']}"
    return f"{source}, topic: {doc.metadata.get('topic', 'unknown')}"


def format_docs(docs, agent_label: str):
    """Return (context_text, unique_source_labels)."""
    blocks, labels = [], []
    for i, doc in enumerate(docs, start=1):
        label = describe_source(doc)
        if label not in labels:
            labels.append(label)
        blocks.append(f"[{agent_label} | source {i}: {label}]\n{doc.page_content}")
    return "\n\n".join(blocks), labels


def make_retrievers(dbs: dict, k: int = 5) -> dict:
    return {agent: make_retriever(dbs[coll], k) for agent, coll in AGENT_COLLECTION.items()}
