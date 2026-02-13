from agno.os import AgentOS

from agents.text2sql import sql_agent
from db.demo_db import demo_db


import os
print("DATABASE_URL =", os.getenv("DATABASE_URL"))


agent_os = AgentOS(
    id="agentos",
    agents=[
        sql_agent,
    ],
)
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="main:app", reload=True)