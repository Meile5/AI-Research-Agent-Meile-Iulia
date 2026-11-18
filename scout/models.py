from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Paper(BaseModel):
    """A paper returned by the search tool."""
    id: str
    title: str
    authors: list[str]
    year: int | None
    citations: int | None
    url: str
    abstract: str = ""
    citation_source: str = "OpenAlex (cited_by_count)"


class Constraints(BaseModel):
    """Constraints extracted from the user's request."""
    topic: str = Field(description="Short search query for the topic, English keywords only")
    year_op: Literal["before", "after", "in"] | None = Field(
        None, description="Only set if the user gave a publication year condition")
    year: int | None = None
    cite_op: Literal["min", "max", "approx"] | None = Field(
        None, description="min = at least, max = at most, approx = around. Only set if the user gave a citation condition")
    cites: int | None = None

    @model_validator(mode="after")
    def _pairs(self):
        if (self.year_op is None) != (self.year is None):
            raise ValueError("year_op and year must be given together")
        if (self.cite_op is None) != (self.cites is None):
            raise ValueError("cite_op and cites must be given together")
        return self


class Pick(BaseModel):
    """What the LLM returns: a paper id and an explanation."""
    found: bool
    paper_id: str | None = None
    explanation: str = Field(description="Why it matches, or why nothing matched. Mention any uncertainty.")


class ResearchAnswer(BaseModel):
    """Final answer, built by code from the tool's data."""
    found: bool
    title: str | None = None
    authors: list[str] = []
    year: int | None = None
    citations: int | None = None
    citation_source: str | None = None
    link: str | None = None
    explanation: str