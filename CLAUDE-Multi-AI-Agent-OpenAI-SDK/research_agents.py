"""Shared agent code for the notebook and the Streamlit app.

Defines the Tavily search tool, the Pydantic output models, the Researcher /
Analyst / Writer agents and the pipeline that chains them.
"""

import asyncio
import json
import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, TypedDict

import requests
from agents import Agent, Runner, SQLiteSession, function_tool
from agents.tool_context import ToolContext
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv(override=True)

MODEL = "gpt-5-mini"
TAVILY_URL = "https://api.tavily.com/search"
DEFAULT_MAX_RESULTS = 2


# ---------------------------------------------------------------- tool
class TavilySearchArgs(TypedDict):
    """Arguments for the Tavily web search."""

    query: str  # The search query
    max_results: int  # Number of results to return (use 2 unless told otherwise)


@function_tool
def tavily_search(args: TavilySearchArgs) -> str:
    """Search the web with Tavily and return titles, URLs and content snippets.

    Args:
        args: The search query and the maximum number of results (default 2).
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY is not set in the environment."

    max_results = args.get("max_results") or DEFAULT_MAX_RESULTS
    try:
        response = requests.post(
            TAVILY_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={"query": args["query"], "max_results": max_results},
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        return f"Error: Tavily search failed: {exc}"

    results = response.json().get("results", [])
    if not results:
        return "No results found."
    return "\n\n".join(
        f"{i}. {r.get('title', '')}\n   URL: {r.get('url', '')}\n   {r.get('content', '')}"
        for i, r in enumerate(results, start=1)
    )


# ---------------------------------------------------------------- output models
class ResearchOutput(BaseModel):
    """Structured output passed between Researcher and Analyst."""

    summary: str


class ReportOutput(BaseModel):
    """Final executive report produced by the Writer."""

    short_summary: str = Field(description="A 2-3 sentence executive summary.")
    markdown_report: str = Field(description="The full report in markdown, at least 500 words.")
    follow_up_questions: list[str] = Field(description="3 to 5 follow-up questions.")


# ---------------------------------------------------------------- agents
researcher = Agent(
    name="Researcher",
    model=MODEL,
    instructions=(
        "You are a web researcher. Use the tavily_search tool to find "
        "real-time, factual information about the user's topic. "
        "Call it with max_results=2 unless told otherwise. "
        "Return at most 5 concise bullet points of facts (one per line, "
        "starting with '- '). Include the source URL in a bullet when relevant. "
        "Do not analyze or speculate; only report what you found."
    ),
    tools=[tavily_search],
    output_type=ResearchOutput,
)

analyst = Agent(
    name="Analyst",
    model=MODEL,
    instructions=(
        "You are an analyst. You receive research notes and must extract the "
        "key trends, risks and insights from them. Write exactly 2 paragraphs. "
        "Use only the information in the notes; do not search the web."
    ),
    output_type=ResearchOutput,
)

writer = Agent(
    name="Writer",
    model=MODEL,
    instructions=(
        "You are a senior report writer. You receive the original user question, "
        "the Researcher's notes and the Analyst's analysis. Write a polished "
        "executive report using only that material. Return: "
        "(1) short_summary: 2-3 sentences; "
        "(2) markdown_report: at least 500 words, with a title, headings "
        "(overview, key findings, trends, risks, conclusion) and the source URLs "
        "mentioned in the research; "
        "(3) follow_up_questions: 3 to 5 questions for further research."
    ),
    output_type=ReportOutput,
)


# ---------------------------------------------------------------- running
# One persistent event loop in a background thread. Reusing it keeps the SDK's
# cached OpenAI client valid across runs (a new loop per call closes it).
_loop = asyncio.new_event_loop()
threading.Thread(target=_loop.run_forever, daemon=True).start()


def run_agent(agent: Agent, user_input: str, session: SQLiteSession | None = None):
    """Run an agent to completion (no `await` needed) and return the RunResult."""
    future = asyncio.run_coroutine_threadsafe(
        Runner.run(agent, user_input, session=session), _loop
    )
    return future.result()


def run_tool(tool, query: str, max_results: int = 2) -> str:
    """Call a function tool directly (outside an agent) for testing."""
    payload = json.dumps({"args": {"query": query, "max_results": max_results}})
    ctx = ToolContext(
        context=None,
        tool_name=tool.name,
        tool_call_id="manual",
        tool_arguments=payload,
    )
    coro = tool.on_invoke_tool(ctx, payload)
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


def writer_input_for(user_query: str, research: ResearchOutput, analysis: ResearchOutput) -> str:
    return (
        f"User question:\n{user_query}\n\n"
        f"Research notes:\n{research.summary}\n\n"
        f"Analysis:\n{analysis.summary}"
    )


def run_pipeline(user_query: str, on_stage: Callable[[str, str], None] | None = None) -> dict:
    """Researcher -> Analyst -> Writer in one shared in-memory SQLiteSession.

    `on_stage(name, state)` is called with state "running" / "done" so a UI can
    show progress. Returns the three outputs plus per-agent timings (seconds).
    """
    session = SQLiteSession(f"research-{uuid.uuid4().hex[:8]}")
    timings: dict[str, float] = {}

    def stage(name: str, agent: Agent, text: str):
        if on_stage:
            on_stage(name, "running")
        start = time.perf_counter()
        out = run_agent(agent, text, session).final_output
        timings[name] = round(time.perf_counter() - start, 1)
        if on_stage:
            on_stage(name, "done")
        return out

    research = stage("Researcher", researcher, user_query)
    analysis = stage("Analyst", analyst, research.summary)
    report = stage("Writer", writer, writer_input_for(user_query, research, analysis))
    return {"research": research, "analysis": analysis, "report": report, "timings": timings}


async def manager_run(user_query: str) -> ReportOutput:
    """Async version of the pipeline: Researcher -> Analyst -> Writer."""
    session = SQLiteSession(f"research-{uuid.uuid4().hex[:8]}")
    research = (await Runner.run(researcher, user_query, session=session)).final_output
    analysis = (await Runner.run(analyst, research.summary, session=session)).final_output
    writer_input = writer_input_for(user_query, research, analysis)
    return (await Runner.run(writer, writer_input, session=session)).final_output


def run_manager(user_query: str) -> ReportOutput:
    """Run manager_run on the persistent loop (no top-level await needed)."""
    return asyncio.run_coroutine_threadsafe(manager_run(user_query), _loop).result()
