import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Database URLs
# ---------------------------------------------------------------------------
MYSQL_URL    = os.getenv("MYSQL_URL", "mysql+pymysql://root:password@localhost:3306/json_insurancedb")
PG_URL       = os.getenv("PG_URL", "postgresql+psycopg2://knowledge:password@localhost:5432/agno_db")
DB_NAME      = os.getenv("DB_NAME", "json_insurancedb")

# ---------------------------------------------------------------------------
# LLM Configuration
# ---------------------------------------------------------------------------
LLM_MODEL    = os.getenv("LLM_MODEL", "gpt-4o-mini")

# ---------------------------------------------------------------------------
# Agent UI
# ---------------------------------------------------------------------------
AGENT_TITLE  = os.getenv("AGENT_TITLE", "Insurance Master AI")
CHART_SERVER_PORT = int(os.getenv("CHART_SERVER_PORT", "7777"))

# ---------------------------------------------------------------------------
# Knowledge Tables (PgVector)
# ---------------------------------------------------------------------------
KNOWLEDGE_TABLE = os.getenv("KNOWLEDGE_TABLE", "json_sql_agent_knowledge_v1")
LEARNINGS_TABLE = os.getenv("LEARNINGS_TABLE", "json_sql_agent_learnings_v1")
