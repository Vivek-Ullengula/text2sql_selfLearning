import os
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use('Agg')
from PIL import Image
from sqlalchemy import create_engine, text as sql_text

from agno.tools import tool
from agno.utils.log import logger
from settings import MYSQL_URL, CHART_SERVER_PORT, LLM_MODEL

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_CHARTS_DIR = _PROJECT_ROOT / "exports" / "charts"
_CHARTS_DIR.mkdir(parents=True, exist_ok=True)
_ENGINE = create_engine(MYSQL_URL)
_PAI_CONFIGURED = False


def _execute_query(sql: str) -> pd.DataFrame:
    """Execute SQL and return a DataFrame."""
    with _ENGINE.connect() as conn:
        return pd.read_sql(sql_text(sql), conn)


def _configure_pandasai():
    """One-time PandasAI setup (lazy init)."""
    global _PAI_CONFIGURED
    if _PAI_CONFIGURED:
        return
    import pandasai as pai
    from pandasai_litellm.litellm import LiteLLM

    pai.config.set({
        "llm": LiteLLM(model=LLM_MODEL, api_key=os.getenv("OPENAI_API_KEY", "")),
        "save_charts": True,
        "save_charts_path": str(_CHARTS_DIR),
        "open_charts": False,
        "enable_cache": False,
    })
    _PAI_CONFIGURED = True


def _add_padding(image_path: Path, padding: int = 200):
    """Add white padding around a chart to prevent UI cropping."""
    with Image.open(image_path) as img:
        canvas = Image.new("RGB", (img.width + 2 * padding, img.height + 2 * padding), "white")
        canvas.paste(img, (padding, padding))
        canvas.save(image_path)


def _find_latest_chart() -> Path | None:
    """Return the most recently saved chart PNG, or None."""
    charts = sorted(_CHARTS_DIR.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
    return charts[0] if charts else None


@tool(show_result=False)
def visualize_last_query_results(
    sql_query: str,
    visualization_request: str = "Generate the most appropriate visualization for this dataset",
) -> str:
    """Generate a chart from SQL query results using PandasAI.

    Call this ONLY when the user asks to visualize/chart/plot data.
    Pass the exact SQL query that was last executed via run_sql_query.
    """
    if not sql_query or not sql_query.strip():
        return "No SQL query provided. Please pass the last executed SQL query."

    if not os.getenv("OPENAI_API_KEY"):
        return "Visualization failed: OPENAI_API_KEY not set."

    # 1. Execute query
    try:
        df = _execute_query(sql_query)
    except Exception as e:
        logger.error(f"SQL execution failed: {e}")
        return f"Failed to execute the query for visualization: {e}"

    if df.empty:
        return "The query returned no rows — nothing to visualize."

    # 2. Generate chart
    try:
        import pandasai as pai
        _configure_pandasai()

        prompt = (
            f"Plot a chart: {visualization_request}. Use matplotlib. "
            "Use Portrait orientation (approx 6x7 inches). "
            "Rotate x-axis labels by 45 degrees. "
            "Call plt.tight_layout(pad=3.0)."
        )
        pai.DataFrame(df).chat(prompt)
    except Exception as e:
        logger.error(f"PandasAI failed: {e}")
        return f"Visualization generation failed: {e}"

    # 3. Find and pad the chart
    chart = _find_latest_chart()
    if not chart:
        return "PandasAI completed but no chart file was found."

    try:
        _add_padding(chart)
    except Exception as e:
        logger.warning(f"Failed to add padding: {e}")

    logger.info(f"Chart saved at: {chart}")
    return (
        "Visualization generated. IMPORTANT: You MUST copy this markdown "
        f"into your response exactly:\n\n"
        f"![Chart](http://localhost:{CHART_SERVER_PORT}/charts/{chart.name})"
    )
