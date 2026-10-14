"""Human reviewers: a console reviewer for real people and a scripted one for tests."""
from src.agents import AGENT_LABELS


def _ask(prompt, allowed=None):
    """Ask until the input is non-empty (and in `allowed`, if given)."""
    while True:
        value = input(prompt).strip()
        if value and (allowed is None or value.lower() in allowed):
            return value.lower() if allowed else value
        print("  Invalid or empty input, please try again.")


def console_reviewer(payload: dict) -> dict:
    if payload["checkpoint"] == "route_review":
        print("\n--- ROUTE REVIEW ---")
        print("Question :", payload["question"])
        print("Detected :", ", ".join(payload["detected_agents"]))
        print("Reason   :", payload["reason"])
        choice = _ask("Approve this split (a) or reject (r)? ", {"a", "r"})
        if choice == "a":
            return {"action": "approve"}
        for number, name in payload["agent_options"].items():
            print(f"  {number}. {name} ({AGENT_LABELS[name]})")
        number = _ask("Press 1-4 to pick the single agent: ", {str(n) for n in payload["agent_options"]})
        return {"action": "reject", "agent_number": int(number)}

    print("\n--- ANSWER REVIEW ---")
    print(f"Agents used: {', '.join(payload['agents'])}   "
          f"(revisions so far: {payload['revision_count']}/{payload['max_revisions']})\n")
    print(payload["draft"])
    choice = _ask("\nApprove (a), edit (e), revise (v) or reject (r)? ", {"a", "e", "v", "r"})
    if choice == "a":
        return {"action": "approve"}
    if choice == "e":
        return {"action": "edit", "edited_answer": _ask("Type the final answer text: ")}
    if choice == "v":
        return {"action": "revise", "feedback": _ask("Type your feedback for the revision: ")}
    return {"action": "reject"}


def scripted_reviewer(*decisions):
    """Return a reviewer that gives `decisions` in order, then approves.

    A decision is a dict such as {"action": "approve"} or {"action": "reject", "agent_number": 2};
    a bare string such as "approve" is shorthand for {"action": "approve"}.
    """
    queue = list(decisions)

    def reviewer(payload: dict) -> dict:
        if queue:
            decision = queue.pop(0)
            return {"action": decision} if isinstance(decision, str) else dict(decision)
        return {"action": "approve"}

    return reviewer
