import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import gradio as gr
from ui.dashboard import create_ui

if __name__ == "__main__":
    app = create_ui()
    # Launch Gradio on 0.0.0.0:7860
    theme = gr.themes.Soft(primary_hue="indigo", secondary_hue="blue")
    app.launch(server_name="127.0.0.1", server_port=7860, share=False, theme=theme)
