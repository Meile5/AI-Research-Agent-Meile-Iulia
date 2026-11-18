import pytest

from scout.models import Constraints, Paper
from scout.verify import violations


def paper(year=2020, citations=100):
    """Small helper so each test only sets the fields it cares about."""
    return Paper(id="W1", title="Test", authors=["A"], year=year, citations=citations, url="https://x")


def ok(p, **constraints):
    return violations(p, Constraints(topic="agents", **constraints)) == []


def test_no_constraints_accepts_anything():
    assert ok(paper(year=None, citations=None))


@pytest.mark.parametrize("year, expected", [(2022, False), (2023, True)])
def test_after_is_strict(year, expected):
    assert ok(paper(year=year), year_op="after", year=2022) is expected


@pytest.mark.parametrize("year, expected", [(2022, False), (2021, True)])
def test_before_is_strict(year, expected):
    assert ok(paper(year=year), year_op="before", year=2022) is expected


@pytest.mark.parametrize("year, expected", [(2021, False), (2022, True), (2023, False)])
def test_in_is_exact(year, expected):
    assert ok(paper(year=year), year_op="in", year=2022) is expected


@pytest.mark.parametrize("cites, expected", [(99, False), (100, True), (101, True)])
def test_min_citations(cites, expected):
    assert ok(paper(citations=cites), cite_op="min", cites=100) is expected


@pytest.mark.parametrize("cites, expected", [(99, True), (100, True), (101, False)])
def test_max_citations(cites, expected):
    assert ok(paper(citations=cites), cite_op="max", cites=100) is expected


@pytest.mark.parametrize("cites, expected", [(79, False), (80, True), (120, True), (121, False)])
def test_approx_citations_within_20_percent(cites, expected):
    assert ok(paper(citations=cites), cite_op="approx", cites=100) is expected


def test_missing_year_is_rejected():
    assert not ok(paper(year=None), year_op="after", year=2020)


def test_missing_citations_is_rejected():
    assert not ok(paper(citations=None), cite_op="min", cites=10)


def test_both_constraints_report_both_problems():
    c = Constraints(topic="agents", year_op="after", year=2022, cite_op="min", cites=100)
    assert len(violations(paper(year=2020, citations=5), c)) == 2


@pytest.mark.parametrize("bad", [
    {"year_op": "after"},
    {"year": 2022},
    {"cite_op": "min"},
    {"cites": 100},
])
def test_constraints_must_come_in_pairs(bad):
    with pytest.raises(ValueError):  # Pydantic wraps it in ValidationError, which is a ValueError
        Constraints(topic="agents", **bad)