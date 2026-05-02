import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import gradio as gr
from ui.dashboard import create_ui, custom_css

if __name__ == "__main__":
    is_space = os.environ.get("SPACE_ID") is not None
    server_name = "0.0.0.0" if is_space else "127.0.0.1"

    app = create_ui()
    app.launch(
        server_name=server_name,
        share=False,
        css=custom_css,
    )