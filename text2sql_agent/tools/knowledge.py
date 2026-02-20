import json
from typing import Optional

from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.text_reader import TextReader
from agno.utils.log import logger

def create_save_validated_query_tool(knowledge_base: Knowledge):
    """Factory to create a save_validated_query tool bound to a specific knowledge base."""

    def save_validated_query(
        name: str,
        question: str,
        query: Optional[str] = None,
        summary: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> str:
        """Save a validated SQL query and its explanation to the knowledge base. Use this when you write a great, reusable query.

        Args:
            name: The name/title of the query.
            question: The original question asked by the user.
            summary: Optional short explanation of what the query does and returns.
            query: The exact SQL query that was executed successfully.
            notes: Optional caveats, assumptions, or data-quality considerations.

        Returns:
            str: Status message.
        """
        if knowledge_base is None:
            return "Knowledge not available"

        sql_stripped = (query or "").strip()
        if not sql_stripped:
            return "No SQL provided"

        # Basic safety: only allow SELECT to be saved
        if not sql_stripped.lower().lstrip().startswith("select"):
            return "Only SELECT queries can be saved"

        payload = {"name": name, "question": question, "query": query, "summary": summary, "notes": notes}

        logger.info("Saving validated SQL query to knowledge base")

        knowledge_base.add_content(
            name=name,
            text_content=json.dumps(payload, ensure_ascii=False),
            reader=TextReader(),
            skip_if_exists=True,
        )

        return "Saved validated query to knowledge base"
    
    # We return the function so it can be used as a Python tool without the @tool decorator wrapping it immediately.
    # We will pass this directly to the agent's tools list.
    return save_validated_query
