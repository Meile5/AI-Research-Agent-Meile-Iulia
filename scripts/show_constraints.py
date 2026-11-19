import sys

from dotenv import load_dotenv

from scout.agent import run

load_dotenv()

answer, deps = run(sys.argv[1])
print("Constraints the agent used:", deps.constraints)
print("Searches:", deps.searches)
print("Answer:", answer.title, answer.year, answer.citations)