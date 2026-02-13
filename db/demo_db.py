# ============================================================================
# Configure database for storing sessions, memories, metrics, evals and knowledge
# ============================================================================
from agno.db.postgres import PostgresDb

# ************* Create database *************
db_url: str = "postgresql+psycopg2://knowledge:password@localhost:5432/agno_db"
demo_db = PostgresDb(id="demo-db", db_url=db_url)
