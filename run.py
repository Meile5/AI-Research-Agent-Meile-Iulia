"""Command line: python run.py "Find a paper about LLM agents after 2022 with at least 100 citations" """
import os
import sys

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")  

import httpx
from pydantic_ai.exceptions import ModelAPIError, ModelRateLimitError, UnexpectedModelBehavior

from scout.agent import ask
from scout.models import ResearchAnswer


def show(a: ResearchAnswer) -> None:
    if not a.found:
        print("No paper found.")
        print(f"Why: {a.explanation}")
        return
    print(f"Title:     {a.title}")
    print(f"Authors:   {', '.join(a.authors) or 'unknown'}")
    print(f"Year:      {a.year}")
    print(f"Citations: {a.citations} (source: {a.citation_source})")
    print(f"Link:      {a.link}")
    print(f"Why:       {a.explanation}")


def main() -> int:
    question = " ".join(sys.argv[1:]) or input("What paper are you looking for? ")
    try:
        show(ask(question))
        return 0
    except ModelRateLimitError:
        print("Groq rate limit reached (429). Wait a minute and try again.")
    except ModelAPIError as e:  
        print(f"Groq rejected the request: {e}")
    except UnexpectedModelBehavior:
        print("The model did not give a valid answer after several retries. Try rephrasing the question.")
    except httpx.HTTPStatusError as e:
        print(f"OpenAlex error {e.response.status_code}. Check OPENALEX_API_KEY in .env, or wait and try again.")
    except RuntimeError as e:  
        print(e)
    return 1


if __name__ == "__main__":
    sys.exit(main())
    