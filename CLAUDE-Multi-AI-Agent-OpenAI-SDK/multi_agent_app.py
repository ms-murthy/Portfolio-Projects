"""Streamlit UI for the Researcher -> Analyst -> Writer pipeline.

Run with:  streamlit run multi_agent_app.py
The agents themselves live in research_agents.py (shared with the notebook).
"""

import os
import re

import pandas as pd
import streamlit as st

from research_agents import MODEL, ReportOutput, run_pipeline

# ---------------------------------------------------------------- UI
st.set_page_config(page_title="Multi-Agent Research", page_icon=":mag:", layout="wide")

# Hide Streamlit's top-right toolbar (Deploy, Rerun, Print, Record screen, ...) and footer.
st.markdown(
    """
    <style>
    [data-testid="stToolbar"], [data-testid="stDeployButton"], #MainMenu, footer {display: none;}
    </style>
    """,
    unsafe_allow_html=True,
)

PAGES = ["Question", "Research", "Analyst", "Writer", "Report"]
PAGE_AGENT = {"Research": "Researcher", "Analyst": "Analyst", "Writer": "Writer", "Report": "Writer"}
EXAMPLES = {
    "Cybertruck reviews": "What is the public sentiment and expert reviews about the Tesla Cybertruck?",
    "Why Labubu is popular": "Why is Labubu so popular and what are the rarest Labubu collectibles?",
    "Quantum computing news": "What are the latest breakthroughs in quantum computing?",
    "EV market outlook": "What is the outlook for the global electric vehicle market?",
}

missing = [k for k in ("OPENAI_API_KEY", "TAVILY_API_KEY") if not os.getenv(k)]
if missing:
    st.error(f"Missing in .env: {', '.join(missing)}")
    st.stop()

# Navigation requests made after the radio was drawn are applied here, before it is drawn.
if "goto" in st.session_state:
    st.session_state["page"] = st.session_state.pop("goto")
st.session_state.setdefault("page", "Question")
st.session_state.setdefault("query_text", EXAMPLES["Cybertruck reviews"])

result = st.session_state.get("result")


def use_example(text: str) -> None:
    st.session_state["query_text"] = text
    st.session_state["page"] = "Question"


def nav_label(name: str) -> str:
    if name == "Question":
        return "Question"
    return f"{name}  ✓" if result else name


# ---------------------------------------------------------------- sidebar (left)
with st.sidebar:
    st.title("Research Pipeline")
    st.caption(f"Researcher → Analyst → Writer · {MODEL}")

    st.radio("Navigate", PAGES, key="page", format_func=nav_label, label_visibility="collapsed")

    st.divider()
    st.subheader("Try an Example")
    for label, text in EXAMPLES.items():
        st.button(label, key=f"ex_{label}", on_click=use_example, args=(text,), width="stretch")

    st.divider()
    st.subheader("How it works")
    st.markdown(
        "1. **Question** – ask anything.\n"
        "2. **Research** – the Researcher searches the web (Tavily) and collects up to 5 facts.\n"
        "3. **Analyst** – extracts trends, risks and insights from those facts.\n"
        "4. **Writer** – turns everything into an executive summary, report and follow-up questions.\n"
        "5. **Report** – read, chart and download the result.\n\n"
        "All three agents share one session memory."
    )

page = st.session_state["page"]
st.title(page)


def need_result() -> bool:
    if result:
        return False
    st.info("No results yet. Go to **Question** and run a research first.")
    return True


# ---------------------------------------------------------------- pages
if page == "Question":
    with st.form("query_form"):
        st.text_area("What do you want to research?", key="query_text", height=110)
        submitted = st.form_submit_button("Run research", type="primary")

    st.caption("Tip: pick a ready-made question under **Try an Example** in the sidebar.")

    if submitted:
        query = st.session_state["query_text"].strip()
        if not query:
            st.warning("Please enter a question.")
            st.stop()

        cols = st.columns(3)
        boxes = [c.empty() for c in cols]
        states = {n: "waiting" for n in ("Researcher", "Analyst", "Writer")}
        icons = {"waiting": "⏳", "running": "🔄", "done": "✅"}

        def render() -> None:
            for box, (name, state) in zip(boxes, states.items()):
                box.markdown(f"### {icons[state]} {name}\n{state.capitalize()}")

        def on_stage(name: str, state: str) -> None:
            states[name] = state
            render()

        render()
        try:
            st.session_state["result"] = run_pipeline(query, on_stage)
            st.session_state["query"] = query
            st.session_state["goto"] = "Report"
            st.rerun()
        except Exception as exc:  # surface API/network errors in the UI
            st.error(f"Pipeline failed: {exc}")

    elif result:
        st.success(f"Last run: \"{st.session_state.get('query', '')}\" — open **Report** in the sidebar.")

elif page == "Research" and not need_result():
    urls = sorted(set(re.findall(r"https?://[^\s)\]>,;]+", result["research"].summary)))
    c1, c2 = st.columns(2)
    c1.metric("Sources found", len(urls))
    c2.metric("Time (s)", result["timings"]["Researcher"])
    st.caption(f"Question: {st.session_state.get('query', '')}")
    st.markdown(result["research"].summary)
    if urls:
        st.subheader("Sources")
        for u in urls:
            st.markdown(f"- {u}")

elif page == "Analyst" and not need_result():
    st.metric("Time (s)", result["timings"]["Analyst"])
    st.markdown(result["analysis"].summary)

elif page == "Writer" and not need_result():
    report: ReportOutput = result["report"]
    c1, c2 = st.columns(2)
    c1.metric("Report words", len(report.markdown_report.split()))
    c2.metric("Time (s)", result["timings"]["Writer"])
    st.subheader("Summary")
    st.info(report.short_summary)
    st.subheader("Follow-up questions")
    for q in report.follow_up_questions:
        st.markdown(f"- {q}")

elif page == "Report" and not need_result():
    report: ReportOutput = result["report"]
    urls = sorted(set(re.findall(r"https?://[^\s)\]>,;]+", result["research"].summary)))

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Report words", len(report.markdown_report.split()))
    m2.metric("Sources found", len(urls))
    m3.metric("Follow-up questions", len(report.follow_up_questions))
    m4.metric("Total time (s)", round(sum(result["timings"].values()), 1))

    st.subheader("Summary")
    st.info(report.short_summary)

    left, right = st.columns([2, 1])
    with left:
        st.subheader("Full report")
        st.markdown(report.markdown_report)
    with right:
        st.subheader("Time per agent (s)")
        st.bar_chart(pd.DataFrame({"seconds": result["timings"]}))
        st.subheader("Follow-up questions")
        for q in report.follow_up_questions:
            st.markdown(f"- {q}")
        if urls:
            st.subheader("Sources")
            for u in urls:
                st.markdown(f"- {u}")

    download = (
        f"# {st.session_state.get('query', 'Research report')}\n\n"
        f"**Summary:** {report.short_summary}\n\n{report.markdown_report}\n\n"
        "## Follow-up questions\n"
        + "\n".join(f"{i}. {q}" for i, q in enumerate(report.follow_up_questions, 1))
    )
    st.download_button("Download report (.md)", download, file_name="research_report.md", mime="text/markdown")
