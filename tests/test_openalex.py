import httpx

from scout.models import Constraints
from scout.openalex import build_filter, rebuild_abstract, search_papers


def test_build_filter_year_and_citations():
    c = Constraints(topic="x", year_op="after", year=2022, cite_op="min", cites=100)
    assert build_filter(c) == "publication_year:>2022,cited_by_count:>99"


def test_build_filter_before_and_max():
    c = Constraints(topic="x", year_op="before", year=2021, cite_op="max", cites=50)
    assert build_filter(c) == "publication_year:<2021,cited_by_count:<51"


def test_build_filter_empty():
    assert build_filter(Constraints(topic="x")) == ""


def test_rebuild_abstract():
    assert rebuild_abstract({"Hello": [0], "world": [1], "again": [2]}) == "Hello world again"
    assert rebuild_abstract(None) == ""


def work(i, year, cites):
    return {
        "id": f"https://openalex.org/W{i}",
        "doi": None,
        "title": f"Paper {i}",
        "publication_year": year,
        "cited_by_count": cites,
        "authorships": [{"author": {"display_name": "A. Author"}}],
        "abstract_inverted_index": {"An": [0], "abstract": [1]},
    }


def mock_client(results):
    handler = lambda request: httpx.Response(200, json={"results": results})
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_search_drops_papers_that_break_constraints():
    client = mock_client([work(1, 2023, 500), work(2, 2019, 900), work(3, 2024, 10)])
    c = Constraints(topic="x", year_op="after", year=2022, cite_op="min", cites=100)
    papers = search_papers(c, client=client)
    assert [p.id for p in papers] == ["W1"]
    assert papers[0].url == "https://openalex.org/W1"
    assert papers[0].abstract == "An abstract"


def test_search_returns_empty_when_nothing_fits():
    client = mock_client([work(1, 2010, 5)])
    c = Constraints(topic="x", year_op="after", year=2022)
    assert search_papers(c, client=client) == []