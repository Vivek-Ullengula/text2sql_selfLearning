from dotenv import load_dotenv
load_dotenv()

from settings import AGENT_TITLE

from agno.os import AgentOS
from text2sql_agent.agent import sql_agent

# Initialize AgentOS with our SQL Agent
# The visualization instructions are now heavily baked into system_prompt.py

from agno.os.config import AgentOSConfig, ChatConfig

agent_os = AgentOS(
    agents=[sql_agent],
    config=AgentOSConfig(
        description="Text-to-SQL Agent with Visualization",
        chat=ChatConfig(
            title=AGENT_TITLE,
            quick_prompts={
                "sql-agent": [
                    "List the top 5 agents (providers) who have the most policies.",
                    "Give me a monthly trend of claims reported in 2024.",
                    "Find all customers who have a vehicle with 'Comprehensive' coverage."
                ]
            }
        )
    )
)

# Get the FastAPI app
app = agent_os.get_app()

# Mount static files for charts
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

# Get absolute path to charts directory (must match visualization.py)
base_dir = Path(__file__).parent.resolve()
charts_dir = base_dir / "exports" / "charts"
charts_dir.mkdir(parents=True, exist_ok=True)

app.mount("/charts", StaticFiles(directory=str(charts_dir)), name="charts")



if __name__ == "__main__":
    # Serve the app
    # Note: "agno_agentos:app" refers to this file and the app variable
    agent_os.serve(app="agno_agentos:app", reload=True)