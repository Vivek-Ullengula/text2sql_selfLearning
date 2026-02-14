import gradio as gr
from agents.text2sql import sql_agent
import os
import re
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

import base64

# ... (Previous imports)

# Load Environment Variables
load_dotenv()

def chat(message, history):
    """
    Chat function for Gradio.
    """
    try:
        # Run the agent with streaming
        response_stream = sql_agent.run(message, stream=True)
        
        partial_response = ""
        
        for chunk in response_stream:
            # 1. Handle Content (Text/Markdown)
            content = getattr(chunk, "content", None)
            if content:
                # Accumulate content
                partial_response += content
                
                # Dynamic Image Path Replacement (Base64 for reliability)
                display_response = partial_response
                
                def replace_image_tag(match):
                    path = match.group(1).strip()
                    # Check if file exists
                    if os.path.exists(path):
                        try:
                            with open(path, "rb") as image_file:
                                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                            return f'![Chart](data:image/png;base64,{encoded_string})'
                        except Exception as e:
                            return f"*[Error loading image: {str(e)}]*"
                    else:
                         return f"*[Image not found at: {path}]*"

                # Only attempt replacement if tag is closed to avoid flicker/errors
                if "]" in display_response:
                     display_response = re.sub(r'\[IMAGE_PATH:(.*?)\]', replace_image_tag, display_response)
                
                yield display_response

            # 2. Handle Tool Calls
            tool_calls = getattr(chunk, "tools", None) or getattr(chunk, "tool_calls", None)
            if tool_calls:
                for tc in tool_calls:
                    t_name = getattr(tc, 'tool_name', None) or getattr(tc, 'function', {}).get('name')
                    if t_name:
                         partial_response += f"\n\n> 🛠️ **Running Tool:** `{t_name}`\n\n"
                         yield partial_response 
            
    except Exception as e:
        yield f"**Error executing agent:** {str(e)}"

# Custom CSS for "Gemini/ChatGPT" Style (Clean, Professional)
custom_css = """
/* Font & Base Settings */
.gradio-container {
    font-family: 'Segoe UI', Helvetica, Arial, sans-serif !important;
    font-size: 16px !important; /* Standard professional size */
}

/* Chat Layout - Centered but Comfortable */
.chatbot {
    max-width: 900px !important; /* Back to 900px for readablity */
    margin: auto !important;
    border: none !important;
    box-shadow: none !important;
}

/* Remove EVERYTHING that looks like a border/container */
.gradio-container .prose, .chatbot, .user, .bot, .message {
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
}

/* Message Specifics */
.user {
    background-color: #f0f0f0 !important; /* Subtle gray */
    padding: 12px 18px !important;
    border-radius: 12px !important;
    margin-bottom: 8px !important;
}
.bot {
    padding: 12px 0 !important; /* No background, just text */
    background-color: transparent !important;
}

/* Avatar Styling */
.avatar-image {
    width: 30px !important;
    height: 30px !important;
}

/* Table Styling - Compact & Scrollable */
.prose table {
    width: auto !important; /* Don't stretch to full width */
    max-width: 100%;
    margin: 1rem 0;
    font-size: 0.9em;
    border-collapse: collapse;
    display: block;
    overflow-x: auto; /* Scroll horizontal if needed */
}
.prose thead tr {
    background-color: #f8f9fa;
    border-bottom: 2px solid #dee2e6;
}
.prose th {
    font-weight: 600;
    color: #495057;
    text-transform: uppercase;
    font-size: 0.8em;
    padding: 10px;
}
.prose td {
    padding: 8px 10px;
    border-bottom: 1px solid #eee;
    color: #333;
}
"""

# Use Blocks for CSS injection
with gr.Blocks(css=custom_css, title="Text2SQL Agent 🤖", theme=gr.themes.Base(radius_size="none", spacing_size="sm")) as app:
    with gr.Column(elem_classes=["chatbot"]): # Apply max-width constraint
        gr.Markdown("# Text2SQL Agent 🤖\nAsk questions about your data.")
        
        chat_interface = gr.ChatInterface(
            fn=chat,
            examples=["Give me 10 customer details", "Show active policies in CA"],
            cache_examples=False,
        )

if __name__ == "__main__":
    print(f"Starting Gradio on Port 7860...")
    app.launch(server_name="0.0.0.0", server_port=7860, show_error=True)
