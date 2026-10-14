"""Wire the live system together: models, vector stores, retrievers and the graph."""
import warnings

# Harmless serializer noise from structured output; the decisions themselves are correct.
warnings.filterwarnings("ignore", message="Pydantic serializer warnings", category=UserWarning)

from src.agents import make_answer_fn, make_rewrite_fn, make_route_fn, make_scope_fn
from src.config import get_embeddings, get_llm
from src.graph import build_graph
from src.retrieval import make_retrievers
from src.vectorstore import load_existing


def build_live_system():
    """Return (graph, scope_fn) using the real model and the four saved collections."""
    llm = get_llm()
    dbs = load_existing(get_embeddings())
    graph = build_graph(
        route_fn=make_route_fn(llm),
        rewrite_fn=make_rewrite_fn(llm),
        answer_fn=make_answer_fn(llm),
        retrievers=make_retrievers(dbs),
    )
    return graph, make_scope_fn(llm)
