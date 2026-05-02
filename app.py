import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import gradio as gr
from ui.dashboard import create_ui, custom_css

if __name__ == "__main__":
    app = create_ui()
    app.launch(
        server_name="127.0.0.1",
        share=False,
        css=custom_css,
    )
