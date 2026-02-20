from agno.db.postgres import PostgresDb
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector, SearchType

# MySQL — CustLight insurance data (queries)
mysql_url: str = "mysql+pymysql://root:password@localhost:3306/custlight"

# PostgreSQL — Agno knowledge base, sessions, memory
pg_url: str = "postgresql+psycopg2://knowledge:password@localhost:5432/agno_db"

def get_demo_db() -> PostgresDb:
    return PostgresDb(id="demo2-db", db_url=pg_url)

import os
from agno.utils.log import logger

def create_knowledge_base(name: str, table_name: str, contents_db: PostgresDb = None) -> Knowledge:
    """Create a Knowledge instance backed by PgVector."""
    
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning(f"OPENAI_API_KEY is not set. Creating {name} with OpenAIEmbedder may fail to generate valid 1536-dimensional embeddings for PgVector.")

    return Knowledge(
        name=name,
        vector_db=PgVector(
            db_url=pg_url,
            table_name=table_name,
            search_type=SearchType.hybrid,
            # We explicitly define the dimensions so PgVector knows what table schema to create
            embedder=OpenAIEmbedder(id="text-embedding-3-small", dimensions=1536),
        ),
        max_results=5,
        contents_db=contents_db,
    )

# The static, curated SQL Knowledge Base
sql_agent_knowledge = create_knowledge_base(
    name="SQL Agent Knowledge",
    table_name="custlight_sql_agent_knowledge_v2",
    contents_db=get_demo_db()
)

# The dynamic, learned knowledge base
sql_agent_learnings = create_knowledge_base(
    name="SQL Agent Learnings",
    table_name="custlight_sql_agent_learnings_v2"
)
