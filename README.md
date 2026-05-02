---
title: AI_Interview_Coach
app_file: app.py
sdk: gradio
sdk_version: 6.14.0
---
# AI Mock Interview Coach

## Project Overview
The **AI Mock Interview Coach** is a production-grade application designed to provide structured, adaptive, and realistic interview simulations. It uses a multi-agent orchestration system to handle candidate intake, dynamic interview planning, real-time speech-to-text processing, and detailed performance evaluation.

The system is built on a deterministic state machine, ensuring that the interview remains professional, goal-oriented, and tailored to the candidate's target role and focus areas.

## Key Features
*   **Intake Profile Builder**: Seamlessly capture your target role and focus areas. Upload your resume (PDF) to ground the interview in your actual experience.
*   **Adaptive Interview Room**:
    *   **Live Webcam Preview**: Stay focused and maintain professional posture with a live camera feed.
    *   **Interactive Chatbot**: Engages you in a realistic dialogue with follow-up questions.
    *   **Dual Input Modes**: Respond using your microphone (powered by AssemblyAI) or type your answers manually.
*   **Intelligent Evaluation & Coaching**:
    *   **Real-time Feedback**: View AI evaluations of your responses, including scoring on correctness, reasoning, and clarity.
    *   **Dynamic Difficulty**: The AI adjusts the challenge level (Easy, Medium, Hard, Expert) based on your performance.
    *   **Topic Tracking**: Monitors your progress across different technical and behavioral domains.
*   **Comprehensive Final Report**: At the end of the session, the system generates a detailed Markdown coaching report with strengths, weaknesses, and actionable improvement tips.

## Tech Stack
*   **Interface**: Gradio (Web-based dashboard)
*   **Language**: Python 3.10+
*   **LLM Orchestration**: Google Gemini (Pro/Flash), Groq (Llama-3), and OpenRouter
*   **Speech-to-Text**: AssemblyAI (Primary), Faster-Whisper (Local Fallback)
*   **Grounding**: Firecrawl API for role/industry research
*   **Data Validation**: Pydantic v2

---

## Setup and Installation

Follow these detailed steps to get the project running on your local machine.

### 1. Clone the Project
Open your terminal or command prompt and run:
```bash
git clone https://github.com/Ayush-D2004/AI-Interview-Coach.git
cd AI-Interview-Coach
```

### 2. Environment Configuration
The application requires several API keys to function. 
1.  Copy the example environment file:
    ```bash
    cp .env.example .env
    ```
2.  Open the `.env` file in a text editor and fill in your keys:
    *   `GEMINI_API_KEY`: Get from [Google AI Studio](https://aistudio.google.com/)
    *   `ASSEMBLYAI_API_KEY`: Get from [AssemblyAI Dashboard](https://www.assemblyai.com/dashboard)
    *   `FIRECRAWL_API_KEY`: (Optional) For real-time grounding.
    *   `GROQ_API_KEY`: (Optional) For fallback models.

### 3. Create and Activate Virtual Environment
We use a virtual environment to manage dependencies.

**On Windows:**
```powershell
python -m venv coach
.\coach\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv coach
source coach/bin/activate
```

### 4. Install Dependencies
Once the environment is active, install the required packages:
```bash
pip install -r requirements.txt
```

---

## Running the Project

1.  **Activate the environment** (if not already active):
    *   Windows: `.\coach\Scripts\activate`
    *   macOS/Linux: `source coach/bin/activate`

2.  **Launch the application**:
    ```bash
    python app.py
    ```

3.  **Access the Dashboard**:
    The terminal will output a local URL (e.g., `http://127.0.0.1:7860`). Open this link in your web browser to start your mock interview.

---

## Usage Guide
1.  **Intake**: Enter your target role (e.g., "Software Engineer") and focus area (e.g., "System Design"). Upload your resume PDF and click **Start Interview**.
2.  **Interviewing**: Read the AI's question in the chat. Use the **Microphone** to record your answer or type it in the text box, then click **Submit Answer**.
3.  **Evaluation**: You can toggle the "Show/Hide AI Evaluation" to see real-time scores for your latest response.
4.  **Reporting**: Once finished, click **Finish Interview & Generate Report** to receive your full performance review at the bottom of the page.

---

## Data Persistence
All session transcripts, metrics, and generated reports are saved locally in the `data/sessions` directory for your review.
