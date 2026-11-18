# Research Scout Agent

A PydanticAI agent that finds a research paper matching a request (topic, year and citation
constraints) using the OpenAlex API, and rejects papers that don't fit.

Demo video: TODO (link)

## How it works

| Step | Who does it |
|---|---|
| Read the request and pull out topic, year and citation constraints | LLM |
| Search OpenAlex with those constraints (`scout/openalex.py`) | Code |
| Check every result against the constraints again (`scout/verify.py`) | Code |
| Pick the best paper and explain why it fits | LLM |
| Check the pick is a real result that satisfies the constraints, otherwise retry | Code |
| Fill in title, authors, year, citations, source and link | Code |

The LLM only returns a paper id and an explanation. Everything else, including the citation
count, comes from OpenAlex, so the model can't make it up.

## LLM

Groq with `openai/gpt-oss-120b`: free, supports tool calling and has an OpenAI-compatible API.
TODO: add the current rate limits and the date we checked them.