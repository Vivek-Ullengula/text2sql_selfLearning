import os
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Force matplotlib to not use any Xwindows backend
from PIL import Image
from sqlalchemy import create_engine, text as sql_text

from agno.tools import tool
from agno.utils.log import logger

# We need the demo_db url to connect via pandas
from db.config import mysql_url

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
    # Save charts in a my_charts folder at the project root
    project_root = Path(__file__).resolve().parent.parent.parent
    charts_dir = project_root / "my_charts"
    charts_dir.mkdir(exist_ok=True)

    try:
        import pandasai as pai
        from pandasai_litellm.litellm import LiteLLM

        # PandasAI v3 Setup
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            return "Visualization failed: OPENAI_API_KEY not set."

        # Configure PandasAI with LiteLLM
        llm = LiteLLM(model="gpt-4o-mini", api_key=api_key)
        pai.config.set({
            "llm": llm,
            "save_charts": True,
            "save_charts_path": str(charts_dir),
            "open_charts": False,
            "enable_cache": False,
            "verbose": False,
            "max_retries": 3,
        })

        # Create SmartDataframe
        sdf = pai.DataFrame(df)

        # Ask PandasAI to generate the visualization
        chart_prompt = (
            f"Plot a chart: {visualization_request}. "
            "Use matplotlib. "
            "IMPORTANT: Use Portrait orientation (approx 6x7 inches). "
            "Rotate x-axis labels by 45 degrees to prevent overlap. "
            "Call plt.tight_layout(pad=3.0) to ensure titls and labels are not cut off. "
            "Save the chart as a PNG file."
        )
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
        
        # 3. Check default exports/charts directory (PandasAI v3 default fallback)
        if not generated_chart_path:
            weights_dir = project_root / "exports" / "charts"
            if weights_dir.exists():
                chart_files_default = sorted(weights_dir.glob("*.png"), key=lambda x: x.stat().st_mtime, reverse=True)
                if chart_files_default:
                   generated_chart_path = chart_files_default[0]

        if generated_chart_path:
            logger.info(f"Chart saved at: {generated_chart_path}")
            
            # --- AgentOS Logic: Add Padding to Prevent UI Cropping ---
            try:
                with Image.open(generated_chart_path) as img:
                    # Create a larger canvas (add 200px border)
                    padding = 200
                    new_width = img.width + (2 * padding)
                    new_height = img.height + (2 * padding)
                    
                    canvas = Image.new("RGB", (new_width, new_height), "white")
                    # Paste original image in the center
                    canvas.paste(img, (padding, padding))
                    canvas.save(generated_chart_path)
            except Exception as e:
                logger.warning(f"Failed to add padding: {e}")

            chart_filename = generated_chart_path.name
            return f"Visualization generated. IMPORTANT: To show this to the user, you MUST copy the following markdown into your response:\n\n![Chart](http://localhost:7777/charts/{chart_filename})\n\n(Saved to: {generated_chart_path})"
        else:
            return f"PandasAI response: {result}. No chart file was generated."

    except Exception as e:
        logger.error(f"PandasAI visualization failed: {e}")
        return f"Visualization generation failed: {e}"
