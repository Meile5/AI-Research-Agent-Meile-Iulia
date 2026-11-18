"""Deterministic checks: does a paper satisfy the user's constraints?"""
from scout.models import Constraints, Paper

APPROX_TOLERANCE = 0.2  # "around 100 citations" accepts 80..120


def violations(p: Paper, c: Constraints) -> list[str]:
    """Return the reasons why p breaks c. An empty list means the paper is acceptable."""
    problems: list[str] = []

    if c.year_op is not None:
        if p.year is None:
            problems.append("publication year is unknown")
        elif c.year_op == "after" and not p.year > c.year:
            problems.append(f"published {p.year}, not after {c.year}")
        elif c.year_op == "before" and not p.year < c.year:
            problems.append(f"published {p.year}, not before {c.year}")
        elif c.year_op == "in" and p.year != c.year:
            problems.append(f"published {p.year}, not in {c.year}")

    if c.cite_op is not None:
        if p.citations is None:
            problems.append("citation count is unknown")
        elif c.cite_op == "min" and p.citations < c.cites:
            problems.append(f"{p.citations} citations, fewer than {c.cites}")
        elif c.cite_op == "max" and p.citations > c.cites:
            problems.append(f"{p.citations} citations, more than {c.cites}")
        elif c.cite_op == "approx" and abs(p.citations - c.cites) > APPROX_TOLERANCE * c.cites:
            problems.append(f"{p.citations} citations, not around {c.cites}")

    return problems