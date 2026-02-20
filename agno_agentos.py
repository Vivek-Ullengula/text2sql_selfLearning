from dotenv import load_dotenv
load_dotenv()

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
            title="CustLight AI",
            quick_prompts={
                "sql-agent": [
                    "List top 5 Producers by Commission on Active Policies",
                    "Give me the monthly trend of Total Commission Amount for the past year",
                    "List high-performing Providers (> $500 comm) with policy counts",
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

# Get absolute path to exports/charts
base_dir = Path(__file__).parent.resolve()
charts_dir = base_dir / "exports" / "charts"
charts_dir.mkdir(parents=True, exist_ok=True)

app.mount("/charts", StaticFiles(directory=str(charts_dir)), name="charts")



if __name__ == "__main__":
    # Serve the app
    # Note: "agno_agentos:app" refers to this file and the app variable
    agent_os.serve(app="agno_agentos:app", reload=True)