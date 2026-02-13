import streamlit as st
import re
from pathlib import Path
from time import time
from text2sql import sql_agent  # adjust if needed

@st.cache_resource
def get_agent():
    return sql_agent

# -----------------------------------------------------------------------------
# Page Config
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SQL Agent",
    layout="wide"
)

st.title("📊 SQL Agent with Visualizations")

# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = "streamlit_session"

# -----------------------------------------------------------------------------
# Display Chat History
# -----------------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if msg.get("image"):
            try:
                with open(msg["image"], "rb") as f:
                    image_bytes = f.read()

                # Center image nicely
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.image(image_bytes, use_container_width=True)

            except FileNotFoundError:
                pass  # Safe fail if image removed

# -----------------------------------------------------------------------------
# Chat Input
# -----------------------------------------------------------------------------
if prompt := st.chat_input("Ask about your insurance data..."):

    # Store user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    # -------------------------------------------------------------------------
    # Assistant Response
    # -------------------------------------------------------------------------
    with st.chat_message("assistant"):

        run_start_time = time()

        # Show spinner only for agent execution
        with st.spinner("Thinking..."):
            agent = get_agent()
            response = agent.run(
                prompt,
                session_id=st.session_state.session_id
            )
        
        run_end_time = time()
        execution_duration = run_end_time - run_start_time

        # ---------------------------------------------------------------------
        # Thinking Process (AgentOS Style Transparency)
        # ---------------------------------------------------------------------
        # Parse tool calls to show "X Tools Called"
        tool_calls = []
        if hasattr(response, 'messages') and response.messages:
             for msg in response.messages:
                 if getattr(msg, 'tool_calls', None):
                     for tc in msg.tool_calls:
                         tool_calls.append(tc)

        tool_count = len(tool_calls)
        tool_label = f"{tool_count} Tool{'s' if tool_count != 1 else ''} Called" if tool_count > 0 else "Direct Response"
        
        with st.expander(f"🧠 Thinking Process ({tool_label} • {execution_duration:.2f}s)", expanded=False):
            if hasattr(response, 'messages') and response.messages:
                for msg in response.messages:
                    # Show Tool Calls (Instructions to Agent)
                    if getattr(msg, 'tool_calls', None):
                        for tc in msg.tool_calls:
                            # Handle dict vs object
                            if isinstance(tc, dict):
                                func_name = tc.get('function', {}).get('name', 'Unknown')
                                func_args = tc.get('function', {}).get('arguments', '{}')
                            else:
                                func_name = tc.function.name
                                func_args = tc.function.arguments

                            st.markdown(f"**🔨 Calling Tool:** `{func_name}`")
                            st.code(func_args, language="json")
                    
                    # Show Tool Outputs (Results from Agent)
                    elif msg.role == "tool":
                        st.markdown(f"**🛠️ Tool Output:** `{msg.name if hasattr(msg, 'name') else 'Result'}`")
                        # Truncate very long outputs for readability
                        content = str(msg.content)
                        if len(content) > 1000:
                            content = content[:1000] + "... (truncated)"
                        st.code(content)
            else:
                st.info("No detailed trace available for this response.")

        # Show text immediately
        st.markdown(response.content)

        # ---------------------------------------------------------------------
        # ---------------------------------------------------------------------
        # Visualization Handling (History Support)
        # ---------------------------------------------------------------------
        # Note: The tool itself (text2sql.py) renders the image immediately via st.image().
        # This block detects the file to save it to session state for HISTORY persistence.
        
        charts_dir = Path("exports/charts")
        image_path = None
        
        if charts_dir.exists():
            # Find the most recent chart
            images = sorted(charts_dir.glob("*.png"), key=lambda x: x.stat().st_mtime, reverse=True)
            if images:
                latest_image = images[0]
                # If generated during this run, store it
                if latest_image.stat().st_mtime >= run_start_time:
                    image_path = str(latest_image)

    # -------------------------------------------------------------------------
    # Save Assistant Message to Session
    # -------------------------------------------------------------------------
    assistant_msg = {
        "role": "assistant",
        "content": response.content
    }

    if image_path:
        assistant_msg["image"] = image_path

    st.session_state.messages.append(assistant_msg)
