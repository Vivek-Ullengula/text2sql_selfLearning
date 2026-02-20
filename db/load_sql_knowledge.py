import sys
from pathlib import Path

# Add project root to sys.path so we can import from agents
sys.path.append(str(Path(__file__).resolve().parent.parent))

from agno.utils.log import logger

from db.config import sql_agent_knowledge

# ============================================================================
# Path to SQL Agent Knowledge
# ============================================================================
cwd = Path(__file__).parent.parent
knowledge_dir = cwd.joinpath("knowledge")

# ============================================================================
# Load SQL Agent Knowledge
# ============================================================================
if __name__ == "__main__":
    logger.info(f"Loading SQL Agent Knowledge from {knowledge_dir}")
    sql_agent_knowledge.add_content(path=str(knowledge_dir))
    logger.info("SQL Agent Knowledge loaded.")
