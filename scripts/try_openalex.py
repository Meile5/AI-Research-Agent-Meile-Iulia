from dotenv import load_dotenv

from scout.models import Constraints
from scout.openalex import search_papers

load_dotenv()

c = Constraints(topic="LLM agents software engineering", year_op="after", year=2022,
                cite_op="min", cites=100)

for p in search_papers(c):
    print(f"{p.id} | year={p.year or '?'} | citations={p.citations if p.citations is not None else '?'} | {p.title}")
    print("   ", p.url)