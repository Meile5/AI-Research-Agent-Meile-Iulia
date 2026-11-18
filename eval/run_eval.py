"""Runs the agent on every prompt in eval/prompts.json and writes eval/results.md.
'Relevant' and 'Useful explanation' are judged by a human, so they are left as ? to fill in.
Run from the repo root:  python -m eval.run_eval
"""
import json
import time
from pathlib import Path

from pydantic_ai.exceptions import AgentRunError

from scout.agent import run
from scout.models import Constraints, Paper
from scout.verify import violations

EVAL_DIR = Path(__file__).parent
PAUSE_SECONDS = 10

def yes_no(ok: bool) -> str:
    return "yes" if ok else "NO"


def evaluate(case: dict) -> str:
    """Run one prompt and return one row of the results table."""
    exp = case["expected"]
    start = f"| {case['id']} | {case['category']} |"
    try:
        answer, deps = run(case["prompt"])
    except AgentRunError as e:
        return f"{start} ERROR: {type(e).name}: {str(e)[:150]} | | | | | ? | ? | | |"  # show the reason too

    found_ok = yes_no(answer.found == exp["should_find"])
    if not answer.found:
        return f"{start} {found_ok} | n/a | n/a | n/a | n/a | ? | ? | {deps.searches} | {answer.explanation} |"

    # Check the answer against what the user asked in prompts.json
    p = Paper(id="answer", title=answer.title, authors=answer.authors, year=answer.year,
              citations=answer.citations, url=answer.link)
    year_ok = not violations(p, Constraints(topic="eval", year_op=exp["year_op"], year=exp["year"]))
    cites_ok = not violations(p, Constraints(topic="eval", cite_op=exp["cite_op"], cites=exp["cites"]))
    source_ok = bool(answer.link) and "OpenAlex" in (answer.citation_source or "")
    real = any(s.url == answer.link and s.year == answer.year and s.citations == answer.citations
               for s in deps.seen.values())

    return (f"{start} {found_ok} | {yes_no(year_ok)} | {yes_no(cites_ok)} | {yes_no(source_ok)} | {yes_no(real)} "
            f"| ? | ? | {deps.searches} | {answer.title} ({answer.year}, {answer.citations} cit.): {answer.explanation} |")


def main():
    cases = json.loads((EVAL_DIR / "prompts.json").read_text(encoding="utf-8-sig"))
    rows = ["| # | Category | Found as expected | Year ok | Citations ok | Valid source | No hallucination "
            "| Relevant | Useful explanation | Tool calls | Answer |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, case in enumerate(cases):
        if i > 0:
            time.sleep(PAUSE_SECONDS)
        print(f"[{case['id']}/{len(cases)}] {case['prompt']}")
        rows.append(evaluate(case))
    (EVAL_DIR / "results.md").write_text("# Evaluation results\n\n" + "\n".join(rows) + "\n", encoding="utf-8")
    print("Wrote eval/results.md")


if __name__ == "__main__":
    main()