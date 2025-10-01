"""Default prompts.

Prompts loaded from static files to enable 100% self-hosted deployment
without runtime dependency on LangSmith Hub API.

Source: backend/prompts_static/
Extracted from: langchain-ai/* namespace on LangSmith Hub (October 1, 2025)
Update: Run backend/prompts_static/update_prompts.sh
"""

from pathlib import Path

# Load prompts from static files
PROMPTS_DIR = Path(__file__).parent.parent / "prompts_static"

ROUTER_SYSTEM_PROMPT = (PROMPTS_DIR / "router.txt").read_text()
GENERATE_QUERIES_SYSTEM_PROMPT = (PROMPTS_DIR / "generate_queries.txt").read_text()
MORE_INFO_SYSTEM_PROMPT = (PROMPTS_DIR / "more_info.txt").read_text()
RESEARCH_PLAN_SYSTEM_PROMPT = (PROMPTS_DIR / "research_plan.txt").read_text()
GENERAL_SYSTEM_PROMPT = (PROMPTS_DIR / "general.txt").read_text()
RESPONSE_SYSTEM_PROMPT = (PROMPTS_DIR / "response.txt").read_text()
