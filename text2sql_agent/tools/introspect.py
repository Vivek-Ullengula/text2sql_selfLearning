from agno.tools import tool
from agno.utils.log import logger
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import DatabaseError, OperationalError

def create_introspect_schema_tool(db_url: str):
    """Create introspect_schema tool with database connection.
    Used by the agent to self-heal when it guesses incorrect tables or columns.
    """
    engine = create_engine(db_url)

    @tool
    def introspect_schema(
        table_name: str | None = None,
        include_sample_data: bool = False,
        sample_limit: int = 5,
    ) -> str:
        """Inspect database schema at runtime. Use this when you get a 'Table/Column not found' error.

        Args:
            table_name: Table to inspect. If None, lists all tables.
            include_sample_data: Whether to include sample rows to understand data formats.
            sample_limit: Number of sample rows to return.
        """
        try:
            insp = inspect(engine)

            if table_name is None:
                # List all tables
                tables = insp.get_table_names() + insp.get_view_names()
                if not tables:
                    return "No tables or views found."

                lines = ["## Tables & Views", ""]
                for t in sorted(tables):
                    try:
                        with engine.connect() as conn:
                            count = conn.execute(text(f'SELECT COUNT(*) FROM `{t}`')).scalar()
                            lines.append(f"- **{t}** ({count:,} rows)")
                    except (OperationalError, DatabaseError):
                        lines.append(f"- **{t}**")
                return "\n".join(lines)

            # Inspect specific table
            tables = insp.get_table_names() + insp.get_view_names()
            if table_name not in tables:
                return f"Table/View '{table_name}' not found. Available: {', '.join(sorted(tables))}"

            lines = [f"## {table_name}", ""]

            # Columns
            cols = insp.get_columns(table_name)
            if cols:
                lines.extend(["### Columns", "", "| Column | Type | Nullable |", "| --- | --- | --- |"])
                for c in cols:
                    nullable = "Yes" if c.get("nullable", True) else "No"
                    lines.append(f"| {c['name']} | {c['type']} | {nullable} |")
                lines.append("")

            # Primary key
            try:
                pk = insp.get_pk_constraint(table_name)
                if pk and pk.get("constrained_columns"):
                    lines.append(f"**Primary Key:** {', '.join(pk['constrained_columns'])}")
                    lines.append("")
            except Exception:
                pass # Views might not report PKs clearly depending on dialect

            # Sample data
            if include_sample_data:
                lines.append("### Sample")
                try:
                    with engine.connect() as conn:
                        result = conn.execute(text(f'SELECT * FROM `{table_name}` LIMIT {sample_limit}'))
                        rows = result.fetchall()
                        col_names = list(result.keys())
                        if rows:
                            lines.append("| " + " | ".join(col_names) + " |")
                            lines.append("| " + " | ".join(["---"] * len(col_names)) + " |")
                            for row in rows:
                                vals = [str(v)[:30] if v else "NULL" for v in row]
                                lines.append("| " + " | ".join(vals) + " |")
                        else:
                            lines.append("_No data_")
                except (OperationalError, DatabaseError) as e:
                    lines.append(f"_Error fetching sample: {e}_")

            return "\n".join(lines)

        except OperationalError as e:
            logger.error(f"Database connection failed: {e}")
            return f"Error: Database connection failed - {e}"
        except DatabaseError as e:
            logger.error(f"Database error: {e}")
            return f"Error: {e}"

    return introspect_schema
