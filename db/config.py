from agno.db.postgres import PostgresDb
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector, SearchType

import os
from agno.utils.log import logger
from settings import MYSQL_URL, PG_URL, KNOWLEDGE_TABLE, LEARNINGS_TABLE

# Re-export for backward compatibility
mysql_url: str = MYSQL_URL
pg_url: str = PG_URL

def get_demo_db() -> PostgresDb:
    return PostgresDb(id="demo2-db", db_url=pg_url)

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
    table_name=KNOWLEDGE_TABLE,
    contents_db=get_demo_db()
)

# The dynamic, learned knowledge base
sql_agent_learnings = create_knowledge_base(
    name="SQL Agent Learnings",
    table_name=LEARNINGS_TABLE
)
