import os

import httpx

from .models import Constraints, Paper
from .verify import violations

API_URL = "https://api.openalex.org/works"
FIELDS = "id,doi,title,publication_year,cited_by_count,authorships,abstract_inverted_index"
MAX_AUTHORS = 20


def build_filter(c: Constraints) -> str:
    """Turn the constraints into an OpenAlex filter string."""
    parts = []
    if c.year_op == "after":
        parts.append(f"publication_year:>{c.year}")
    elif c.year_op == "before":
        parts.append(f"publication_year:<{c.year}")
    elif c.year_op == "in":
        parts.append(f"publication_year:{c.year}")

    if c.cite_op and c.cites > 0:
        if c.cite_op == "min":
            parts.append(f"cited_by_count:>{c.cites - 1}")
        elif c.cite_op == "max":
            parts.append(f"cited_by_count:<{c.cites + 1}")
        elif c.cite_op == "approx":
            # lower bound only because the upper bound is checked in code by verify.py
            parts.append(f"cited_by_count:>{int(c.cites * 0.8) - 1}")
    return ",".join(parts)


def rebuild_abstract(inverted: dict[str, list[int]] | None) -> str:
    """OpenAlex sends abstracts as {word: [positions]}, so put the words back in order."""
    if not inverted:
        return ""
    words = {}
    for word, positions in inverted.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words[i] for i in sorted(words))


def to_paper(work: dict) -> Paper:
    authors = [
        a["author"]["display_name"]
        for a in work.get("authorships", [])
        if a.get("author", {}).get("display_name")
    ]
    return Paper(
        id=work["id"].rsplit("/", 1)[-1],
        title=work.get("title") or "(untitled)",
        authors=authors[:MAX_AUTHORS],
        year=work.get("publication_year"),
        citations=work.get("cited_by_count"),
        url=work.get("doi") or work["id"],
        abstract=rebuild_abstract(work.get("abstract_inverted_index")),
    )


def search_papers(
    c: Constraints,
    client: httpx.Client | None = None,
    limit: int = 15,
    keep: int = 5,
) -> list[Paper]:
    """Search OpenAlex, then re-check every result with verify.py and keep the first few that pass."""
    params = {"search": c.topic, "per-page": limit, "select": FIELDS}
    flt = build_filter(c)
    if flt:
        params["filter"] = flt
    key = os.getenv("OPENALEX_API_KEY")
    if key:
        params["api_key"] = key

    own_client = client is None
    client = client or httpx.Client(timeout=20)
    try:
        resp = client.get(API_URL, params=params)
        resp.raise_for_status()
    finally:
        if own_client:
            client.close()

    papers = [to_paper(w) for w in resp.json().get("results", [])]
    return [p for p in papers if not violations(p, c)][:keep]