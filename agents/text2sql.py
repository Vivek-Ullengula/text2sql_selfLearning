import json
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from agno.agent import Agent
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.text_reader import TextReader
from agno.models.openai import OpenAIResponses
from agno.tools.reasoning import ReasoningTools
from agno.tools.sql import SQLTools
from agno.utils.log import logger
from agno.vectordb.pgvector import PgVector, SearchType

from agno.db.postgres import PostgresDb

import os
import uuid
from agno.tools import tool

import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server use
import streamlit as st
from sqlalchemy import create_engine, text as sql_text
from openai import OpenAI as OpenAIClient
from pathlib import Path
from typing import Optional

from agno.learn import (
    LearnedKnowledgeConfig,
    LearningMachine,
    LearningMode,
    UserMemoryConfig,
    UserProfileConfig,
)

load_dotenv()

# ============================================================================
# Database Connections
# ============================================================================
# MySQL — CustLight insurance data (queries)
mysql_url: str = "mysql+pymysql://root:password@localhost:3306/custlight"

# PostgreSQL — Agno knowledge base, sessions, memory
pg_url: str = "postgresql+psycopg2://knowledge:password@localhost:5432/agno_db"

demo_db = PostgresDb(id="demo2-db", db_url=pg_url)
sql_agent_knowledge = Knowledge(
    name="SQL Agent Knowledge",
    vector_db=PgVector(
        db_url=pg_url,
        table_name="custlight_sql_agent_knowledge",
        search_type=SearchType.hybrid,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    ),
    max_results=5,
    contents_db=demo_db
)

# 2. Dynamic Learnings (Discovered: errors, user corrections)
agent_learnings = Knowledge(
    name="Agent Learnings",
    vector_db=PgVector(
        db_url=pg_url,
        table_name="custlight_agent_learnings",
        search_type=SearchType.hybrid,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    ),
    contents_db=PostgresDb(id="agent-learnings", db_url=pg_url),
)

# ============================================================================
# Semantic Model — CustLight Insurance Database
# ============================================================================
# Describes the MySQL views that flatten EAV lookup tables into normal columns.
# The agent queries these views to answer questions about customers, policies, etc.

semantic_model = {
    "tables": [
        {
            "table_name": "v_customers",
            "table_description": "Customer details view. Each row is one customer with all attributes as columns.",
            "columns": [
                {"name": "customer_id", "type": "INT", "description": "Unique customer ID (e.g. 1, 2, 3)"},
                {"name": "customer_name", "type": "VARCHAR", "description": "Full customer name (e.g. 'SALTPRINCETON', 'WELLSFARGO', 'CHRISGAYLE')"},
                {"name": "status", "type": "VARCHAR", "description": "Customer status (e.g. 'ACTIVE')"},
                {"name": "customer_number", "type": "VARCHAR", "description": "Customer number identifier"},
                {"name": "email", "type": "VARCHAR", "description": "Email address (e.g. 'ACME@GMAIL.COM')"},
                {"name": "phone", "type": "VARCHAR", "description": "Primary phone number"},
                {"name": "city", "type": "VARCHAR", "description": "Billing city (e.g. 'CASSSTMONTEREY', 'SANDIMAS')"},
                {"name": "state", "type": "VARCHAR", "description": "Billing state (e.g. 'CA')"},
                {"name": "zip_code", "type": "VARCHAR", "description": "Billing ZIP code"},
                {"name": "address", "type": "VARCHAR", "description": "Lookup address"},
                {"name": "tax_id", "type": "VARCHAR", "description": "Tax ID"},
                {"name": "provider_ref", "type": "VARCHAR", "description": "Provider ID (FK to v_providers.provider_id)"},
                {"name": "add_date", "type": "VARCHAR", "description": "Date customer was added"},
                {"name": "add_user", "type": "VARCHAR", "description": "User who added the customer"},
            ],
        },
        {
            "table_name": "v_policies",
            "table_description": "Policy details view. Each row is one insurance policy with all attributes as columns.",
            "columns": [
                {"name": "policy_id", "type": "INT", "description": "Unique policy ID"},
                {"name": "policy_number", "type": "VARCHAR", "description": "Policy number (e.g. 'MLP00000001')"},
                {"name": "policy_display_number", "type": "VARCHAR", "description": "Display policy number"},
                {"name": "status", "type": "VARCHAR", "description": "Policy status ('ACTIVE' or 'CANCELLED')"},
                {"name": "status_code", "type": "VARCHAR", "description": "Status code"},
                {"name": "customer_ref", "type": "VARCHAR", "description": "Customer ID (FK to v_customers.customer_id). Stored as string — use CAST(customer_ref AS UNSIGNED) for joins."},
                {"name": "provider_ref", "type": "VARCHAR", "description": "Provider ID (FK to v_providers.provider_id). Stored as string."},
                {"name": "expiration_date", "type": "VARCHAR", "description": "Expiration date in YYYYMMDD format (e.g. '20270203')"},
                {"name": "index_name", "type": "VARCHAR", "description": "Policy index name"},
                {"name": "quote_number", "type": "VARCHAR", "description": "Quote number"},
                {"name": "transaction_code", "type": "VARCHAR", "description": "Transaction code"},
                {"name": "city", "type": "VARCHAR", "description": "City"},
                {"name": "state", "type": "VARCHAR", "description": "State code"},
                {"name": "postal_code", "type": "VARCHAR", "description": "Postal code"},
                {"name": "email", "type": "VARCHAR", "description": "Contact email"},
                {"name": "contact_number", "type": "VARCHAR", "description": "Contact phone number"},
                {"name": "tax_id", "type": "VARCHAR", "description": "Tax ID"},
            ],
        },
        {
            "table_name": "v_providers",
            "table_description": "Provider/producer details view. Each row is one insurance provider, agent, or financial institution.",
            "columns": [
                {"name": "provider_id", "type": "INT", "description": "Unique provider ID"},
                {"name": "provider_name", "type": "VARCHAR", "description": "Provider name (e.g. 'AGENTBILLPRODUCERI')"},
                {"name": "provider_type", "type": "VARCHAR", "description": "Type: 'PRODUCER' or 'FINANCIAL INSTITUTION'"},
                {"name": "provider_number", "type": "VARCHAR", "description": "Provider number"},
                {"name": "business_name", "type": "VARCHAR", "description": "Business name"},
                {"name": "personal_name", "type": "VARCHAR", "description": "Personal name (if individual)"},
                {"name": "status_code", "type": "VARCHAR", "description": "Status code"},
                {"name": "city", "type": "VARCHAR", "description": "City"},
                {"name": "state", "type": "VARCHAR", "description": "State code (e.g. 'CA')"},
                {"name": "postal_code", "type": "VARCHAR", "description": "Postal code"},
                {"name": "street_address", "type": "VARCHAR", "description": "Street address"},
                {"name": "phone", "type": "VARCHAR", "description": "Phone number"},
                {"name": "tax_id", "type": "VARCHAR", "description": "Tax ID"},
                {"name": "producer_agency", "type": "VARCHAR", "description": "Producer agency"},
                {"name": "producer_group", "type": "VARCHAR", "description": "Producer group"},
            ],
        },
        {
            "table_name": "v_commissions",
            "table_description": "Commission payment records. Each row is one commission record.",
            "columns": [
                {"name": "commission_id", "type": "INT", "description": "Primary key"},
                {"name": "commission_amount", "type": "DECIMAL", "description": "Commission dollar amount"},
                {"name": "premium_amount", "type": "DECIMAL", "description": "Written premium amount"},
                {"name": "transaction_date", "type": "DATE", "description": "Effective date of transaction"},
                {"name": "provider_ref", "type": "VARCHAR", "description": "Provider ID (FK to v_providers.provider_id)"},
                {"name": "policy_ref", "type": "VARCHAR", "description": "Policy ID (FK to v_policies.policy_id)"},
                {"name": "policy_number", "type": "VARCHAR", "description": "Policy Number"},
                {"name": "commission_type", "type": "VARCHAR", "description": "Type of commission"},
                {"name": "carrier_code", "type": "VARCHAR", "description": "Carrier code"},
                {"name": "charged_amount", "type": "DECIMAL", "description": "Charged amount"},
            ],
        },
    ],
    "relationships": [
        {
            "description": "Customer to Policy",
            "join": "v_policies.customer_ref = v_customers.customer_id (use CAST(v_policies.customer_ref AS UNSIGNED) = v_customers.customer_id)",
            "example": "SELECT c.customer_name, p.policy_number, p.status FROM v_policies p JOIN v_customers c ON c.customer_id = CAST(p.customer_ref AS UNSIGNED)",
        },
        {
            "description": "Customer to Provider",
            "join": "v_customers.provider_ref = v_providers.provider_id (use CAST(v_customers.provider_ref AS UNSIGNED) = v_providers.provider_id)",
            "example": "SELECT c.customer_name, pr.provider_name FROM v_customers c JOIN v_providers pr ON pr.provider_id = CAST(c.provider_ref AS UNSIGNED)",
        },
        {
            "description": "Policy to Provider",
            "join": "v_policies.provider_ref = v_providers.provider_id",
            "example": "SELECT p.policy_number, pr.provider_name FROM v_policies p JOIN v_providers pr ON pr.provider_id = CAST(p.provider_ref AS UNSIGNED)",
        },
        {
            "description": "Commission to Provider",
            "join": "v_commissions.provider_ref = v_providers.provider_id",
        },
        {
            "description": "Commission to Policy",
            "join": "v_commissions.policy_ref = v_policies.policy_id",
        },
    ],
}

semantic_model_str = json.dumps(semantic_model, indent=2)

#Tools to add info to knowledge base
def save_validated_query(
    name: str,
    question: str,
    query: Optional[str] = None,
    summary: Optional[str] = None,
    notes: Optional[str] = None,
) -> str:
    """Save a validated SQL query and its explanation to the knowledge base.

    Args:
        name: The name of the query.
        question: The original question asked by the user.
        summary: Optional short explanation of what the query does and returns.
        query: The exact SQL query that was executed.
        notes: Optional caveats, assumptions, or data-quality considerations.

    Returns:
        str: Status message.
    """
    if sql_agent_knowledge is None:
        return "Knowledge not available"

    sql_stripped = (query or "").strip()
    if not sql_stripped:
        return "No SQL provided"

    # Basic safety: only allow SELECT to be saved
    if not sql_stripped.lower().lstrip().startswith("select"):
        return "Only SELECT queries can be saved"

    payload = {"name": name, "question": question, "query": query, "summary": summary, "notes": notes}

    logger.info("Saving validated SQL query to knowledge base")

    sql_agent_knowledge.add_content(
        name=name,
        text_content=json.dumps(payload, ensure_ascii=False),
        reader=TextReader(),
        skip_if_exists=True,
    )

    return "Saved validated query to knowledge base"


@tool(show_result=False)
def visualize_last_query_results(sql_query: str, visualization_request: str = "Generate the most appropriate visualization for this dataset") -> str:
    """Generate a visualization from SQL query results using PandasAI and save as PNG.

    Call this tool ONLY when the user explicitly asks to visualize, chart, or plot
    the data from a SQL query. You MUST pass the SQL query that was most recently
    executed via run_sql_query.

    Args:
        sql_query: The exact SQL query that was last executed via run_sql_query.
        visualization_request: What kind of chart or visualization the user wants
            (e.g. "bar chart of customers by state", "pie chart of policy types").
            Defaults to auto-selecting the best chart type.

    Returns:
        A formatted string describing the result.
        IMPORTANT: If successful, the string includes `[IMAGE_PATH:/path/to/chart.png]`.
        You MUST include this tag VERBATIM in your final response to the user.
    """
    if not sql_query or not sql_query.strip():
        return "No SQL query provided. Please pass the last executed SQL query."

    logger.info(f"Re-executing SQL for visualization: {sql_query}")

    # ── 1. Re-execute the query to get a DataFrame ────────────────────────
    try:
        engine = create_engine(mysql_url)
        with engine.connect() as conn:
            df = pd.read_sql(sql_text(sql_query), conn)
    except Exception as e:
        logger.error(f"Failed to re-execute SQL: {e}")
        return f"Failed to execute the query for visualization: {e}"

    if df.empty:
        return "The query returned no rows — nothing to visualize."

    # ── 2. Use PandasAI to generate the chart ─────────────────────────────
    charts_dir = Path(__file__).resolve().parent / "my_charts"
    charts_dir.mkdir(exist_ok=True)

    try:
        import pandasai as pai
        from pandasai_litellm.litellm import LiteLLM

        # PandasAI v3 Setup
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            return "Visualization failed: OPENAI_API_KEY not set."

        # Configure PandasAI with LiteLLM
        llm = LiteLLM(model="gpt-5-mini", api_key=api_key)
        pai.config.set({
            "llm": llm,
            "save_charts": True,
            "save_charts_path": str(charts_dir),
            "open_charts": False,
            "enable_cache": False,
            "verbose": False,
            "max_retries": 3,
        })

        # Create SmartDataframe (v3 alias is pai.DataFrame)
        sdf = pai.DataFrame(df)

        # Ask PandasAI to generate the visualization
        chart_prompt = f"Plot a chart: {visualization_request}. Save the chart as a PNG file."
        result = sdf.chat(chart_prompt)

        logger.info(f"PandasAI visualization result: {result}")

        # Check if a new chart was saved
        generated_chart_path = None
        
        # 1. Check if result is a file path
        if isinstance(result, str) and str(result).lower().endswith('.png'):
            potential_path = Path(result).resolve()
            if potential_path.exists():
                generated_chart_path = potential_path

        # 2. Check configured charts_dir
        if not generated_chart_path:
            chart_files = sorted(charts_dir.glob("*.png"), key=lambda x: x.stat().st_mtime, reverse=True)
            if chart_files:
                generated_chart_path = chart_files[0]
        
        # 3. Check default exports/charts directory (PandasAI v3 default)
        if not generated_chart_path:
            weights_dir = Path("exports/charts").resolve()
            if weights_dir.exists():
                chart_files_default = sorted(weights_dir.glob("*.png"), key=lambda x: x.stat().st_mtime, reverse=True)
                if chart_files_default:
                   generated_chart_path = chart_files_default[0]

        if generated_chart_path:
            logger.info(f"Chart saved at: {generated_chart_path}")
            
            # Direct rendering in Streamlit (Safe for API)
            try:
                import streamlit as st
                st.image(str(generated_chart_path), caption=f"Visualization: {visualization_request}", width=600)
            except ImportError:
                pass # Streamlit not installed
            except Exception as e:
                # Likely running outside Streamlit context
                logger.warning(f"Skipping Streamlit image render: {e}")

            return f"Visualization generated successfully and saved to {generated_chart_path}"
        else:
            return f"PandasAI response: {result}. No chart file was generated."

    except Exception as e:
        logger.error(f"PandasAI visualization failed: {e}")
        return f"Visualization generation failed: {e}"


@tool(show_result=False)
def export_query_results(sql_query: str) -> str:
    """Export the results of a SQL query to a CSV file.
    
    Args:
        sql_query: The exact SQL query to execute and export.
        
    Returns:
        str: Status message with [EXPORT_PATH:...] tag.
    """
    if not sql_query or not sql_query.strip():
        return "No SQL query provided."
        
    try:
        engine = create_engine(mysql_url)
        with engine.connect() as conn:
            df = pd.read_sql(sql_text(sql_query), conn)
            
        if df.empty:
            return "Query returned no results to export."
            
        # Ensure exports directory exists
        exports_dir = Path("exports").resolve()
        exports_dir.mkdir(exist_ok=True)
        
        # unique filename
        filename = f"export_{uuid.uuid4().hex[:8]}.csv"
        path = exports_dir / filename
        
        df.to_csv(path, index=False)
        return f"Successfully exported {len(df)} rows. [EXPORT_PATH:{path}]"
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        return f"Export failed: {e}"


# ============================================================================
# Instructions (Dash Persona)
# ============================================================================

instructions_list = [
    "Use the views v_customers, v_policies, v_providers, v_commissions for all queries.",
    
    # RESPONSE RULES (CRITICAL)
    "1. **NEW DATA RETRIEVAL**: If you ran a new `run_sql_query`: ",
    "   - MUST show the **Data Table** (Markdown).",
    "   - MUST show the **SQL Query** (```sql ... ```).",
    "   - MUST show **Insights**.",
    
    "2. **VISUALIZATION/EXPORT**: If the user asks to visualize or export *existing* data:",
    "   - Call the tool (`visualize_last_query_results` or `export_query_results`).",
    "   - Return the tool output (Image/Path).",
    "   - **DO NOT** reprint the Data Table or SQL Query.",
    "   - **DO NOT** generate new insights unless the visualization reveals something new.",

    "If the query is NEW, ask: 'Would you like to save this query?'.",
    "Check `search_knowledge_base` AND `search_learnings` before every query.",
    "If you fix an error, use `save_learning` to remember the fix.",
]

system_message = f"""\
You are a self-learning Data Analyst Agent for CustLight Insurance.
Your goal is not just to run queries, but to provide actionable insights.

## Your Purpose
You don't just fetch data. You interpret it.
You explain trends, highligh anomalies, and contextulize numbers.
You remember your past mistakes and get smarter with every query.

## Two Knowledge Systems
**Knowledge** (Static): Validated queries, schema rules.
**Learnings** (Dynamic): Patterns, error fixes, user preferences you discover.

## Workflow
1.  **Search**: Check `search_knowledge_base` and `search_learnings`.
2.  **Think**: Plan your SQL based on the schema and past learnings.
3.  **Execute**: Run the query.
4.  **Analyze**: 
    -   Did it work? If not, fix it and `save_learning`.
    -   What does the data say? 
    -   "Sales are up 20%" is data. "Sales are up 20%, driven by Policy X in CA" is an insight.
5.  **Visualize**: If helpful, plot it.
6.  **Export**: If asked, create a CSV.

## SQL Rules
- Default LIMIT 50.
- Use explicit JOINs/CASTs.
- NO SELECT *.

## RESPONSE FORMAT (STRICT)
1.  **Insights**: Brief analysis of the data (1-2 sentences).
2.  **Data Table**: Markdown Table of the results. (NEVER use list format).
3.  **SQL Query**: The exact query used, in a ```sql``` block.
4.  **Follow-up**: Ask if they want to save or visualize.

## SEMANTIC MODEL
{semantic_model_str}
"""

#Creating agent
sql_agent = Agent(
    id="sql-agent",
    name="SQL Agent",
    model=OpenAIResponses(id="gpt-5-mini"),
    db=demo_db,
    # Knowledge (Static)
    knowledge=sql_agent_knowledge,
    search_knowledge=True,
    # Learning Machine (Dynamic)
    learning=LearningMachine(
        knowledge=agent_learnings,
        user_profile=UserProfileConfig(mode=LearningMode.AGENTIC),
        user_memory=UserMemoryConfig(mode=LearningMode.AGENTIC),
        learned_knowledge=LearnedKnowledgeConfig(mode=LearningMode.AGENTIC),
    ),
    system_message=system_message,
    instructions=instructions_list,
    tools=[
        SQLTools(
            db_url=mysql_url,
            tables={
                "v_customers": "Customer details — columns: customer_id, customer_name, status, email, phone, city, state, zip_code, provider_ref",
                "v_policies": "Policy details — columns: policy_id, policy_number, status, customer_ref, provider_ref, expiration_date",
                "v_providers": "Provider details — columns: provider_id, provider_name, provider_type, city, state, phone",
                "v_commissions": "Commission records — columns: commission_id, commission_amount, transaction_date, provider_ref",
            },
        ),
        ReasoningTools(add_instructions=True),
        visualize_last_query_results,
        save_validated_query,
        export_query_results,
    ],
    add_datetime_to_context=True,
    add_history_to_context=True,
    num_history_runs=5,
    read_chat_history=True,
    read_tool_call_history=True,
    markdown=True,
)
