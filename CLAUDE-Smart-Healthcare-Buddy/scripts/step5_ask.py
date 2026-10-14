"""Step 5: run one question through the whole workflow."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.app import build_live_system  # noqa: E402
from src.graph import run_question  # noqa: E402
from src.reviewers import console_reviewer, scripted_reviewer  # noqa: E402


def parse_route(value):
    if value == "approve":
        return {"action": "approve"}
    if value.startswith("reject:") and value[7:] in {"1", "2", "3", "4"}:
        return {"action": "reject", "agent_number": int(value[7:])}
    sys.exit("--route must be 'approve' or 'reject:<1-4>'")


def parse_answer(value):
    if value in ("approve", "reject"):
        return {"action": value}
    if value.startswith("edit:") and value[5:].strip():
        return {"action": "edit", "edited_answer": value[5:].strip()}
    if value.startswith("revise:") and value[7:].strip():
        return {"action": "revise", "feedback": value[7:].strip()}
    sys.exit("--answer must be approve | reject | edit:<text> | revise:<feedback>")


parser = argparse.ArgumentParser()
parser.add_argument("question")
parser.add_argument("--route")
parser.add_argument("--answer", action="append")
args = parser.parse_args()

if args.route is None and args.answer is None:
    reviewer = console_reviewer
else:
    route_reviewer = scripted_reviewer(*([parse_route(args.route)] if args.route else []))
    answer_reviewer = scripted_reviewer(*[parse_answer(a) for a in (args.answer or [])])

    def reviewer(payload):
        return (route_reviewer if payload["checkpoint"] == "route_review" else answer_reviewer)(payload)

graph, scope_fn = build_live_system()
result = run_question(graph, args.question, reviewer, scope_fn=scope_fn)

print("\n=== RESULT ===")
print("status :", result["status"])
print("agents :", ", ".join(result["agents"]) or "-")
print("\nFinal answer:\n" + result["final_answer"])
print("\nReview log:")
for i, entry in enumerate(result["review_log"], start=1):
    print(f" {i}. [{entry['checkpoint']}] {entry['action']} - {entry['detail']}")
if not result["review_log"]:
    print(" -")
