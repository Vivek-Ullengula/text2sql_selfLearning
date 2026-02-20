from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools.reasoning import ReasoningTools
from agno.tools.sql import SQLTools

from agno.learn import (
    LearnedKnowledgeConfig,
    LearningMachine,
    LearningMode,
)

from db.config import mysql_url, get_demo_db, sql_agent_knowledge, sql_agent_learnings
from text2sql_agent.context.system_prompt import SYSTEM_MESSAGE
from text2sql_agent.tools import (
    create_introspect_schema_tool,
    create_save_validated_query_tool,
    visualize_last_query_results,
)

# ---------------------------------------------------------------------------
# Tools Configuration
# ---------------------------------------------------------------------------
save_validated_query = create_save_validated_query_tool(sql_agent_knowledge)
introspect_schema = create_introspect_schema_tool(mysql_url)

sql_tools = [
    SQLTools(
        db_url=mysql_url,
        tables={
            "v_customers": "Customer details — columns: customer_id, customer_name, status, email, phone, city, state, zip_code, provider_ref",
            "v_policies": "Policy details — columns: policy_id, policy_number, status, customer_ref, provider_ref, expiration_date",
            "v_providers": "Provider/producer details — columns: provider_id, provider_name, provider_type, city, state, phone",
            "v_commissions": "Commission records — columns: commission_id, commission_amount, premium_amount, transaction_date, provider_ref",
            "v_claims": "Claim details — columns: claim_id, claim_number, status, total_incurred, loss_date, reported_date, policy_ref",
            "v_payments": "Payment details — columns: payment_id, policy_ref, amount, payment_date, payment_type",
            "v_notes": "Notes — columns: note_id, policy_ref, claim_ref, author, note_date, note_text",
        },
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
    model=OpenAIResponses(id="gpt-4o-mini"),
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
