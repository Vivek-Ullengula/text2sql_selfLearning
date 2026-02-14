import streamlit as st
from agents.text2sql import sql_agent
import base64
import os
import re
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

st.set_page_config(page_title="Text2SQL Agent", layout="wide")

st.title("Text2SQL Agent 🤖")

# --- Helper Functions ---
def encode_image_base64(path):
    """Encodes a local image to Base64 for Markdown embedding."""
    try:
        if os.path.exists(path):
            with open(path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return f"data:image/png;base64,{encoded_string}"
    except Exception as e:
        print(f"Error encoding image: {e}")
    return None

def process_markdown_images(text):
    """Replaces [IMAGE_PATH:...] with Base64 Markdown images."""
    def replace_tag(match):
        path = match.group(1).strip()
        base64_data = encode_image_base64(path)
        if base64_data:
            return f"![Chart]({base64_data})"
        return f"*[Image not found: {path}]*"
    
    return re.sub(r'\[IMAGE_PATH:(.*?)\]', replace_tag, text)

# --- Chat Logic ---

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # We process images here too to ensure history renders correctly
        st.markdown(process_markdown_images(message["content"]))
        
        # Check for Export in History
        export_match = re.search(r'\[EXPORT_PATH:(.*?)\]', message["content"])
        if export_match:
            export_path = export_match.group(1).strip()
            if os.path.exists(export_path):
                with open(export_path, "rb") as f:
                    st.download_button(
                        label="📂 Download Export (CSV)",
                        data=f,
                        file_name=os.path.basename(export_path),
                        mime="text/csv",
                        key=f"history_download_{export_path}"
                    )

# Custom CSS for ChatGPT-like feel
st.markdown("""
<style>
    /* Remove top padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    /* Hide Deploy button */
    .stDeployButton {
        display: none;
    }
    /* Chat Input Styling */
    .stChatInput {
        padding-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Generator for Smooth Streaming
def stream_response(prompt):
    """Yields chunks of text/tools for st.write_stream"""
    stream = sql_agent.run(prompt, stream=True)
    
    full_buffer = ""
    
    for chunk in stream:
        # 1. Text Content
        content = getattr(chunk, "content", None)
        if content:
            # We buffer to handle split tokens if needed, but for simplicity yield directly
            # Check if we have an image tag incoming? 
            # It's safer to yield text as is, and let the final render handle Base64.
            # BUT st.write_stream renders incrementally. 
            # If we yield `[IMAGE_PATH:...`, it shows that text.
            # We can try to intercept it?
            # Complexity: High. 
            # Simple approach: Yield content. If it contains `[IMAGE_PATH:...]`, user sees it briefly.
            # Better: Yield content.
            full_buffer += content
            yield content
        
        # 2. Tool Calls
        tool_calls = getattr(chunk, "tools", None) or getattr(chunk, "tool_calls", None)
        if tool_calls:
            for tc in tool_calls:
                t_name = getattr(tc, 'tool_name', None) or getattr(tc, 'function', {}).get('name')
                if t_name:
                    tool_msg = f"\n\n> 🛠️ **Running Tool:** `{t_name}`\n\n"
                    full_buffer += tool_msg
                    yield tool_msg

# User Input
if prompt := st.chat_input("Ask about your data..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Use st.write_stream for typing effect
        # It automatically handles the generator yield
        full_response = st.write_stream(stream_response(prompt))
        
        # Final Polish: Check for Images/Exports and Re-render if needed
        # 1. Images
        if "[IMAGE_PATH:" in full_response:
             st.rerun() 
        
        # 2. Exports
        # We use Regex to find [EXPORT_PATH:...]
        export_match = re.search(r'\[EXPORT_PATH:(.*?)\]', full_response)
        if export_match:
            export_path = export_match.group(1).strip()
            if os.path.exists(export_path):
                with open(export_path, "rb") as f:
                    st.download_button(
                        label="📂 Download Export (CSV)",
                        data=f,
                        file_name=os.path.basename(export_path),
                        mime="text/csv"
                    )
        
    # Append to history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
