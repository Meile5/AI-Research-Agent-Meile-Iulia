"""The Research Scout agent: the LLM parses the request and picks a paper, code checks everything."""
from dataclasses import dataclass, field

from pydantic_ai import Agent, ModelRetry, PromptedOutput, RunContext
from pydantic_ai.usage import UsageLimits

from scout import openalex
from scout.config import build_model
from scout.models import Constraints, Paper, Pick, ResearchAnswer
from scout.verify import violations

SYSTEM_PROMPT = """You help users find one research paper.
Rules:
1. Always call search_papers first. Put the user's conditions in its arguments.
   Only set year or citation conditions the user actually gave.
2. Only pick a paper id that search_papers returned. Never invent papers.
3. Never write citation counts, years or authors in your explanation. The system adds them from the tool.
4. If no returned paper fits, answer found=false and explain why.
5. If the request is vague (e.g. "recent", "lots of citations"), say how you interpreted it."""


@dataclass
class Deps:
    """State for one run, shared between the tool and the validator."""
    seen: dict[str, Paper] = field(default_factory=dict)  
    constraints: Constraints | None = None  
    searches: int = 0  


agent = Agent(
    deps_type=Deps,
    output_type=PromptedOutput(Pick),  
    system_prompt=SYSTEM_PROMPT,
    retries=2,  
)


@agent.tool
def search_papers(ctx: RunContext[Deps], constraints: Constraints) -> list[dict]:
    """Search OpenAlex for papers. Returns only papers that already satisfy the constraints."""
    papers = openalex.search_papers(constraints)
    ctx.deps.constraints = constraints
    ctx.deps.searches += 1
    for p in papers:
        ctx.deps.seen[p.id] = p
    return [{"id": p.id, "title": p.title, "year": p.year, "citations": p.citations,
             "abstract": p.abstract[:400]} for p in papers]


@agent.output_validator
def check_pick(ctx: RunContext[Deps], pick: Pick) -> Pick:
    """Code double-checks the LLM's choice. ModelRetry sends the message back so the LLM can fix it."""
    if ctx.deps.constraints is None:
        raise ModelRetry("You must call search_papers before answering.")
    if not pick.found:
        return pick  
    paper = ctx.deps.seen.get(pick.paper_id)
    if paper is None:
        raise ModelRetry(f"Paper id {pick.paper_id!r} was not returned by search_papers. Pick one of those ids.")
    problems = violations(paper, ctx.deps.constraints)
    if problems:
        raise ModelRetry(f"That paper breaks the constraints: {'; '.join(problems)}. Pick another or answer found=false.")
    return pick


def run(question: str, model=None) -> tuple[ResearchAnswer, Deps]:
    """Run the agent and build the final answer from the tool's data, not from the LLM."""
    deps = Deps()
    result = agent.run_sync(question, deps=deps, model=model or build_model(),
                            usage_limits=UsageLimits(request_limit=6))
    pick = result.output
    if not pick.found:
        return ResearchAnswer(found=False, explanation=pick.explanation), deps

    p = deps.seen[pick.paper_id]
    answer = ResearchAnswer(found=True, title=p.title, authors=p.authors, year=p.year,
                            citations=p.citations, citation_source=p.citation_source,
                            link=p.url, explanation=pick.explanation)
    return answer, deps


def ask(question: str, model=None) -> ResearchAnswer:
    """Simple version for run.py: just the answer."""
    return run(question, model)[0]