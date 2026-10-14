"""Streamlit UI for Smart Healthcare Buddy.  Run:  streamlit run streamlit_app.py"""
import json
import uuid

import pandas as pd
import streamlit as st
from langgraph.types import Command

from src.agents import AGENT_LABELS, AGENT_NAMES
from src.app import build_live_system
from src.graph import OUT_OF_SCOPE_MESSAGE, finished_result, start_state

st.set_page_config(page_title="Smart Healthcare Buddy", page_icon="🩺", layout="wide")

SOURCE_TO_AGENT = {
    "finance_reporting_agent.json": "finance_agent",
    "hr_policy_agent.json": "hr_agent",
    "supply_chain_agent.json": "supply_chain_agent",
    "Trends, prospects, challenges, and security in HIOT.pdf": "HIOT_agent",
}
GREEN, GREY = "#2e9e6b", "#d9dde3"


@st.cache_resource(show_spinner="Loading models and vector stores...")
def get_system():
    return build_live_system()


# ---------------------------------------------------------------- helpers
def flow_diagram(used, multi: bool) -> str:
    """Graphviz picture of the workflow with the agents that ran highlighted."""
    def style(active):
        return f'style=filled, fillcolor="{GREEN if active else GREY}", fontcolor="{"white" if active else "#555"}"'

    lines = [
        "digraph G { rankdir=LR; bgcolor=transparent; node [shape=box, style=rounded, fontname=Helvetica]; edge [color=\"#888\"];",
        f'Q [label="Question", {style(True)}]; S [label="Scope check", {style(True)}]; '
        f'SUP [label="Supervisor", {style(True)}];',
        f'R [label="Route review\\n(human)", {style(multi)}];',
        f'A [label="Draft answer", {style(bool(used))}]; AR [label="Answer review\\n(human)", {style(bool(used))}];',
        "Q -> S -> SUP; SUP -> R [style=dashed];",
    ]
    for name in AGENT_NAMES:
        lines.append(f'{name} [label="{AGENT_LABELS[name]}", {style(name in used)}];')
        lines.append(f"SUP -> {name}; R -> {name} [style=dashed]; {name} -> A;")
    lines.append("A -> AR; }")
    return "\n".join(lines)


def cited_by_department(sources) -> pd.DataFrame:
    counts = {AGENT_LABELS[a]: 0 for a in AGENT_NAMES}
    for label in sources:
        agent = SOURCE_TO_AGENT.get(label.split(",")[0])
        if agent:
            counts[AGENT_LABELS[agent]] += 1
    return pd.DataFrame({"Department": list(counts), "Sources cited": list(counts.values())}).set_index("Department")


def to_markdown(question, result) -> str:
    log = "\n".join(f"{i}. [{e['checkpoint']}] {e['action']} - {e['detail']}" for i, e in enumerate(result["review_log"], 1))
    return (
        f"# Smart Healthcare Buddy\n\n**Question:** {question}\n\n"
        f"**Agents used:** {', '.join(AGENT_LABELS[a] for a in result['agents']) or '-'}\n\n"
        f"## Answer\n\n{result['final_answer']}\n\n## Review log\n\n{log or '-'}\n"
    )


def reset():
    for key in ("phase", "config", "payload", "question", "result", "error"):
        st.session_state.pop(key, None)


def advance(out):
    """Store the graph output: either the next checkpoint or the finished result."""
    if "__interrupt__" in out:
        st.session_state.payload = out["__interrupt__"][0].value
        st.session_state.phase = "review"
    else:
        st.session_state.result = finished_result(out)
        st.session_state.phase = "done"


def resume(graph, decision):
    try:
        advance(graph.invoke(Command(resume=decision), st.session_state.config))
    except Exception as exc:  # show the type only; messages can contain sensitive details
        st.session_state.error = f"Something went wrong ({type(exc).__name__}). Please try again."
    st.rerun()


# ------------------------------------------------------------------- page
st.title("🩺 Smart Healthcare Buddy")
st.caption("Ask about Finance Reporting, HR Policy, Supply Chain or the Healthcare IoT research paper. "
           "You review the routing (when several departments are involved) and the final answer.")

try:
    graph, scope_fn = get_system()
except Exception as exc:
    st.error(f"Could not start the system: {exc}")
    st.stop()

phase = st.session_state.get("phase", "idle")
if st.session_state.get("error"):
    st.error(st.session_state.pop("error"))

# ---- 1. ask
if phase == "idle":
    with st.form("ask"):
        question = st.text_area("Your question", placeholder="e.g. What is the general process for requesting paid time off?")
        asked = st.form_submit_button("Ask", type="primary")
    if asked:
        question = question.strip()
        if not question:
            st.warning("Please type a question.")
        else:
            try:
                with st.spinner("Checking scope and routing..."):
                    if not scope_fn(question):
                        st.session_state.question = question
                        st.session_state.result = {"status": "out_of_scope", "final_answer": OUT_OF_SCOPE_MESSAGE,
                                                   "agents": [], "sources": [], "review_log": []}
                        st.session_state.phase = "done"
                    else:
                        st.session_state.question = question
                        st.session_state.config = {"configurable": {"thread_id": str(uuid.uuid4())}}
                        advance(graph.invoke(start_state(question), st.session_state.config))
            except Exception as exc:
                st.session_state.error = f"Something went wrong ({type(exc).__name__}). Please try again."
            st.rerun()

# ---- 2. human checkpoints
elif phase == "review":
    payload = st.session_state.payload
    st.markdown(f"**Question:** {st.session_state.question}")

    if payload["checkpoint"] == "route_review":
        st.subheader("Checkpoint 1 - Route review")
        st.info("This question touches several departments: "
                + ", ".join(AGENT_LABELS[a] for a in payload["detected_agents"]) + f"\n\n*{payload['reason']}*")
        with st.form("route"):
            choice = st.radio("Your decision", ["Approve - split the question across these departments",
                                                "Reject - send it to a single department"])
            agent = st.selectbox("If rejecting, which department?", AGENT_NAMES,
                                 format_func=lambda a: f"{AGENT_NAMES.index(a) + 1}. {AGENT_LABELS[a]}")
            if st.form_submit_button("Submit decision", type="primary"):
                resume(graph, {"action": "approve"} if choice.startswith("Approve")
                       else {"action": "reject", "agent_number": AGENT_NAMES.index(agent) + 1})
    else:
        st.subheader("Checkpoint 2 - Answer review")
        st.caption(f"Agents used: {', '.join(AGENT_LABELS[a] for a in payload['agents'])}  |  "
                   f"revisions so far: {payload['revision_count']} of {payload['max_revisions']}")
        st.markdown(payload["draft"])
        with st.form("answer"):
            action = st.radio("Your decision", ["Approve", "Edit", "Revise", "Reject"], horizontal=True)
            edited = st.text_area("If editing: the final answer text", value=payload["draft"], height=200)
            feedback = st.text_input("If revising: your feedback for the next draft")
            if st.form_submit_button("Submit decision", type="primary"):
                if action == "Edit" and not edited.strip():
                    st.warning("The edited answer cannot be empty.")
                elif action == "Revise" and not feedback.strip():
                    st.warning("Please type feedback for the revision.")
                else:
                    decision = {"action": action.lower()}
                    if action == "Edit":
                        decision["edited_answer"] = edited.strip()
                    if action == "Revise":
                        decision["feedback"] = feedback.strip()
                    with st.spinner("Working..."):
                        resume(graph, decision)

# ---- 3. result
else:
    result, question = st.session_state.result, st.session_state.question
    used = result["agents"]
    if result["status"] == "out_of_scope":
        st.warning(result["final_answer"])
    else:
        revisions = sum(1 for e in result["review_log"] if e["action"] == "revise")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Status", result["status"].capitalize())
        c2.metric("Departments used", len(used))
        c3.metric("Sources cited", len(result["sources"]))
        c4.metric("Revisions", revisions)

        st.subheader("How your question travelled")
        multi = any(e["checkpoint"] == "route_review" for e in result["review_log"])
        st.graphviz_chart(flow_diagram(used, multi), width="stretch")

        tab_answer, tab_sources, tab_log = st.tabs(["Answer", "Sources", "Review log"])
        with tab_answer:
            st.markdown(result["final_answer"])
        with tab_sources:
            if result["sources"]:
                st.bar_chart(cited_by_department(result["sources"]), y="Sources cited", color=GREEN)
                for label in result["sources"]:
                    st.markdown(f"- {label}")
            else:
                st.write("No sources were cited.")
        with tab_log:
            for i, e in enumerate(result["review_log"], 1):
                st.markdown(f"{i}. **{e['checkpoint']}** - {e['action']} - {e['detail']}")

        d1, d2, _ = st.columns([1, 1, 4])
        d1.download_button("Download .md", to_markdown(question, result), "answer.md", "text/markdown")
        d2.download_button("Download .json", json.dumps({"question": question, **result}, indent=2),
                           "answer.json", "application/json")

    st.button("Ask another question", on_click=reset, type="primary")
