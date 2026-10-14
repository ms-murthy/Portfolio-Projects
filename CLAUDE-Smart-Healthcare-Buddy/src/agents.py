"""Decision functions. Each takes the llm as an argument so tests can pass a fake."""
from typing import Literal

from pydantic import BaseModel, Field

from src.prompts import ANSWER_PROMPT, SCOPE_PROMPT, SPLIT_PROMPT, SUPERVISOR_PROMPT

AGENT_NAMES = ["finance_agent", "hr_agent", "supply_chain_agent", "HIOT_agent"]
AGENT_LABELS = {
    "finance_agent": "Finance Reporting",
    "hr_agent": "HR Policy",
    "supply_chain_agent": "Supply Chain",
    "HIOT_agent": "Healthcare IoT (HIOT) research paper",
}

AgentName = Literal["finance_agent", "hr_agent", "supply_chain_agent", "HIOT_agent"]


class ScopeDecision(BaseModel):
    approved: Literal["YES", "NO"]


class RoutingDecision(BaseModel):
    relevant_agents: list[AgentName] = Field(description="Agents the question touches; usually just one.")
    next_agent: AgentName = Field(description="The single most relevant agent.")
    reason: str = Field(description="One sentence explaining the routing.")


def _text(message) -> str:
    content = getattr(message, "content", message)
    return str(content).strip()


def make_scope_fn(llm):
    chain = SCOPE_PROMPT | llm.with_structured_output(ScopeDecision)

    def scope_fn(question: str) -> bool:
        return chain.invoke({"question": question}).approved == "YES"

    return scope_fn


def make_route_fn(llm):
    chain = SUPERVISOR_PROMPT | llm.with_structured_output(RoutingDecision)

    def route_fn(question: str):
        decision = chain.invoke({"question": question})
        # Keep valid names only, no duplicates, in the canonical order.
        candidates = [a for a in AGENT_NAMES if a in decision.relevant_agents]
        next_agent = decision.next_agent
        if next_agent not in candidates:
            candidates.append(next_agent)
        return candidates, next_agent, decision.reason

    return route_fn


def make_rewrite_fn(llm):
    chain = SPLIT_PROMPT | llm

    def rewrite_fn(agent: str, question: str) -> str:
        return _text(chain.invoke({"agent_label": AGENT_LABELS[agent], "question": question}))

    return rewrite_fn


def make_answer_fn(llm):
    chain = ANSWER_PROMPT | llm

    def answer_fn(context: str, question: str, feedback: str, agents) -> str:
        if len(agents) > 1:
            format_rule = (
                "The context comes from more than one department ("
                + ", ".join(AGENT_LABELS[a] for a in agents)
                + "): write one consolidated answer with a short heading per department "
                "and a brief combined takeaway."
            )
        else:
            format_rule = (
                "The context comes from one department only: write a plain answer with no "
                "headings and no takeaway or summary line."
            )
        return _text(chain.invoke({
            "context": context,
            "question": question,
            "feedback": feedback or "none",
            "format_rule": format_rule,
        }))

    return answer_fn
