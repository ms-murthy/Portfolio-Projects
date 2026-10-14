"""The LangGraph workflow: supervisor, two human checkpoints, parallel retrieval, answer."""
import operator
import uuid
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import Command, interrupt

from src.agents import AGENT_LABELS, AGENT_NAMES
from src.retrieval import format_docs

MAX_REVISIONS = 2
OUT_OF_SCOPE_MESSAGE = (
    "Sorry, that question is outside what I can answer. I only cover Finance Reporting, "
    "HR Policy, Supply Chain and the Healthcare IoT (HIOT) research paper."
)
REJECTED_MESSAGE = "The reviewer did not approve this answer."


class AgentState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    query: str
    sub_queries: dict
    selected_agent: str
    candidate_agents: list
    route_reason: str
    route_mode: str
    retrieved_context: Annotated[list, operator.add]
    sources: list
    draft_answer: str
    human_feedback: str
    revision_count: int
    review_log: Annotated[list, operator.add]


def build_graph(route_fn, rewrite_fn, answer_fn, retrievers, checkpointer=None):
    # ---- supervisor -------------------------------------------------------
    def supervisor(state: AgentState):
        candidates, next_agent, reason = route_fn(state["query"])
        multi = len(candidates) > 1
        return {
            "candidate_agents": candidates,
            "selected_agent": next_agent if multi else candidates[0],
            "route_reason": reason,
            "route_mode": "multi" if multi else "single",
        }

    def after_supervisor(state: AgentState):
        return "route_review" if state["route_mode"] == "multi" else state["selected_agent"]

    # ---- human checkpoint 1: route review ---------------------------------
    def route_review(state: AgentState) -> Command[Literal["split_query", "rewrite_query"]]:
        decision = interrupt({
            "checkpoint": "route_review",
            "question": state["query"],
            "detected_agents": state["candidate_agents"],
            "reason": state["route_reason"],
            "actions": ["approve", "reject"],
            "agent_options": {i + 1: name for i, name in enumerate(AGENT_NAMES)},
        })
        if decision.get("action") == "approve":
            return Command(
                goto="split_query",
                update={"review_log": [{
                    "checkpoint": "route_review", "action": "approve",
                    "detail": ", ".join(state["candidate_agents"]),
                }]},
            )
        number = int(decision.get("agent_number", 0))
        if not 1 <= number <= len(AGENT_NAMES):
            raise ValueError("agent_number must be between 1 and 4")
        chosen = AGENT_NAMES[number - 1]
        return Command(
            goto="rewrite_query",
            update={
                "selected_agent": chosen,
                "review_log": [{
                    "checkpoint": "route_review", "action": "reject", "detail": f"human chose {chosen}",
                }],
            },
        )

    # ---- query rewriting --------------------------------------------------
    def split_query(state: AgentState):
        return {"sub_queries": {a: rewrite_fn(a, state["query"]) for a in state["candidate_agents"]}}

    def after_split(state: AgentState):
        return list(state["candidate_agents"])

    def rewrite_query(state: AgentState) -> Command:
        agent = state["selected_agent"]
        return Command(
            goto=agent,
            update={"sub_queries": {agent: rewrite_fn(agent, state["query"])}},
        )

    # ---- one retrieval node per agent -------------------------------------
    def make_agent_node(agent):
        def node(state: AgentState):
            question = (state.get("sub_queries") or {}).get(agent) or state["query"]
            docs = retrievers[agent].invoke(question)
            context, labels = format_docs(docs, AGENT_LABELS[agent])
            return {"retrieved_context": [{"agent": agent, "context": context, "sources": labels}]}
        return node

    # ---- answer -----------------------------------------------------------
    def answer(state: AgentState):
        entries = state["retrieved_context"]
        context = "\n\n".join(e["context"] for e in entries)
        agents = [e["agent"] for e in entries]
        draft = answer_fn(context, state["query"], state.get("human_feedback", ""), agents)
        # List only the retrieved sources that the answer text actually cites.
        labels = []
        for e in entries:
            for label in e["sources"]:
                if label not in labels and f"[{label}]" in draft:
                    labels.append(label)
        if labels:
            draft += "\n\nSources:\n" + "\n".join(f"- {label}" for label in labels)
        return {"draft_answer": draft, "sources": labels}

    # ---- human checkpoint 2: answer review --------------------------------
    def answer_review(state: AgentState) -> Command[Literal["answer", "__end__"]]:
        count = state.get("revision_count", 0)
        decision = interrupt({
            "checkpoint": "answer_review",
            "draft": state["draft_answer"],
            "agents": [e["agent"] for e in state["retrieved_context"]],
            "revision_count": count,
            "max_revisions": MAX_REVISIONS,
            "actions": ["approve", "edit", "revise", "reject"],
        })
        action = decision.get("action")

        def finish(text, detail):
            return Command(goto=END, update={
                "messages": [AIMessage(content=text)],
                "review_log": [{"checkpoint": "answer_review", "action": action, "detail": detail}],
            })

        if action == "approve":
            return finish(state["draft_answer"], "approved as drafted")
        if action == "edit":
            return finish(decision.get("edited_answer") or state["draft_answer"], "reviewer edited the answer")
        if action == "revise":
            if count >= MAX_REVISIONS:
                return finish(
                    state["draft_answer"],
                    f"revision limit ({MAX_REVISIONS}) reached; latest draft released",
                )
            feedback = decision.get("feedback", "")
            return Command(goto="answer", update={
                "human_feedback": feedback,
                "revision_count": count + 1,
                "review_log": [{"checkpoint": "answer_review", "action": "revise", "detail": feedback}],
            })
        return finish(REJECTED_MESSAGE, "reviewer rejected the answer")

    # ---- wiring -----------------------------------------------------------
    builder = StateGraph(AgentState)
    builder.add_node("supervisor", supervisor)
    builder.add_node("route_review", route_review)
    builder.add_node("split_query", split_query)
    builder.add_node("rewrite_query", rewrite_query)
    for agent in AGENT_NAMES:
        builder.add_node(agent, make_agent_node(agent))
    builder.add_node("answer", answer)
    builder.add_node("answer_review", answer_review)

    builder.add_edge(START, "supervisor")
    builder.add_conditional_edges("supervisor", after_supervisor, ["route_review", *AGENT_NAMES])
    builder.add_conditional_edges("split_query", after_split, AGENT_NAMES)
    for agent in AGENT_NAMES:
        builder.add_edge(agent, "answer")
    builder.add_edge("answer", "answer_review")

    return builder.compile(checkpointer=checkpointer or InMemorySaver())


def make_result(status, final_answer="", agents=None, sources=None, review_log=None) -> dict:
    return {
        "status": status,
        "final_answer": final_answer,
        "agents": agents or [],
        "sources": sources or [],
        "review_log": review_log or [],
    }


def start_state(question: str) -> dict:
    return {
        "messages": [HumanMessage(content=question)],
        "query": question,
        "sub_queries": {},
        "revision_count": 0,
        "human_feedback": "",
    }


def finished_result(out: dict) -> dict:
    """Turn the final graph state into the result dict."""
    log = out.get("review_log", [])
    rejected = bool(log) and log[-1]["checkpoint"] == "answer_review" and log[-1]["action"] == "reject"
    return make_result(
        "rejected" if rejected else "completed",
        out["messages"][-1].content,
        [e["agent"] for e in out.get("retrieved_context", [])],
        out.get("sources", []),
        log,
    )


def run_question(graph, question, reviewer, scope_fn=None, thread_id=None) -> dict:
    """Run one question end to end, answering both checkpoints through `reviewer`."""
    question = (question or "").strip()
    if not question:
        return make_result("empty", "Please type a question.")
    if scope_fn is not None and not scope_fn(question):
        return make_result("out_of_scope", OUT_OF_SCOPE_MESSAGE)

    config = {"configurable": {"thread_id": thread_id or str(uuid.uuid4())}}
    out = graph.invoke(start_state(question), config)
    while "__interrupt__" in out:
        payload = out["__interrupt__"][0].value
        out = graph.invoke(Command(resume=reviewer(payload)), config)
    return finished_result(out)
