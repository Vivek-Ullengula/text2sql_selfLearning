import json
from pathlib import Path

from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools.reasoning import ReasoningTools
from agno.tools.sql import SQLTools

from agno.learn import (
    LearnedKnowledgeConfig,
    LearningMachine,
    LearningMode,
)

from settings import MYSQL_URL, LLM_MODEL
from db.config import mysql_url, get_demo_db, sql_agent_knowledge, sql_agent_learnings
from text2sql_agent.context.system_prompt import SYSTEM_MESSAGE
from text2sql_agent.tools import (
    create_introspect_schema_tool,
    create_save_validated_query_tool,
    visualize_last_query_results,
)

# ---------------------------------------------------------------------------
# Auto-load table hints from knowledge/*.json
# ---------------------------------------------------------------------------
def _load_table_hints() -> dict:
    """Build SQLTools table hints from knowledge JSON files.
    Falls back to empty dict if knowledge dir doesn't exist."""
    hints = {}
    knowledge_dir = Path(__file__).resolve().parent.parent / "knowledge"
    if not knowledge_dir.exists():
        return hints
    for fp in sorted(knowledge_dir.glob("*.json")):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
            name = data.get("table_name", fp.stem)
            desc = data.get("table_description", "")
            # Append rules as extra context
            rules = data.get("rules", [])
            if rules:
                desc += " Rules: " + " | ".join(rules)
            hints[name] = desc
        except (json.JSONDecodeError, KeyError):
            continue
    return hints

# ---------------------------------------------------------------------------
# Tools Configuration
# ---------------------------------------------------------------------------
save_validated_query = create_save_validated_query_tool(sql_agent_knowledge)
introspect_schema = create_introspect_schema_tool(mysql_url)

sql_tools = [
    SQLTools(
        db_url=mysql_url,
        tables=_load_table_hints(),
    ),
    ReasoningTools(add_instructions=True),
    visualize_last_query_results,
    save_validated_query,
    introspect_schema,
]

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
sql_agent = Agent(
    id="sql-agent",
    name="SQL Agent",
    model=OpenAIResponses(id=LLM_MODEL),
    db=get_demo_db(),
    system_message=SYSTEM_MESSAGE,
    
    # Static Curated Knowledge
    knowledge=sql_agent_knowledge,
    search_knowledge=True,
    
    # Dynamic Learned Knowledge (The Dash LearningMachine)
    learning=LearningMachine(
        knowledge=sql_agent_learnings,
        learned_knowledge=LearnedKnowledgeConfig(mode=LearningMode.AGENTIC),
    ),
    
    enable_agentic_memory=True,
    tools=sql_tools,
    add_datetime_to_context=True,
    add_history_to_context=True,
    num_history_runs=5,
    read_chat_history=True,
    read_tool_call_history=True,
    markdown=True,
)
