## LLM

Groq with `openai/gpt-oss-120b`: free, supports tool calling and has an OpenAI-compatible API.
The free tier has a low tokens-per-minute limit, so the eval waits 10 seconds between prompts.

## Setup

Requires Python 3.12+. Run everything from the repo root.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## API keys

Copy `.env.example` to `.env` and fill in both keys. `.env` is gitignored, never commit it.

```
LLM_API_KEY=your-groq-key         
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=openai/gpt-oss-120b
OPENALEX_API_KEY=your-openalex-key 
```

## How to run

```powershell
python run.py "Find a paper about LLM agents published after 2022 with at least 100 citations"
python -m pytest -q          
python -m eval.run_eval    
```

## Evaluation

12 prompts in `eval/prompts.json` cover broad and narrow topics, before/after/exact year,
min and max citations, impossible requests and vague requests.

Code checks per prompt: found or rejected as expected, year ok, citations ok, valid source,
no hallucination (the answer matches a paper the tool really returned).
We judged relevance and explanation quality by hand, because code can't judge that.

Result: 11 of 12 as expected. The one failure was "transformer architecture",
where keyword search returned power transformer papers. Full table: `eval/results.md`.

## Contributions

**Iulia** wrote the deterministic check in `scout/verify.py` that decides if a paper breaks the year
or citation rules, with tests for all the edge cases. She wrote the 12 eval prompts, the Groq
setup in `scout/config.py`, and the agent itself in `scout/agent.py`, with offline tests using a fake
model. She also built the command line tool `run.py` and wrote the reflection. When the real eval
showed problems with Groq, she fixed the agent so it accepts both answer formats.

**Meile** wrote `scout/openalex.py`, which searches OpenAlex and turns the results into papers. She
built the eval harness in `eval/run_eval.py`, ran the evaluation and judged the relevance and
explanations by hand. She also set up the README.