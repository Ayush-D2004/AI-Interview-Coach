---
title: AI_Interview_Coach
app_file: app.py
sdk: gradio
sdk_version: 6.14.0
---

# AI Interview Coach

## Project Overview
The **AI Interview Coach** is designed to provide structured, adaptive, and realistic interview simulations. By leveraging a multi-agent orchestration system, it delivers a goal-oriented experience tailored to each candidate's target role, seniority level, and technical expertise.

## System Architecture
The application uses a specialized multi-agent design where each agent handles a specific phase of the interview lifecycle. A central Interview Orchestrator manages the deterministic state machine to ensure a professional and consistent flow.

### Agent Roles

*   **Profile Agent**: Analyzes candidate intake data that includes target roles, focus areas, and uploaded resumes—to construct a comprehensive internal candidate profile.
*   **Grounding Agent**: Uses real-time web search tools to identify current industry standards, role-specific expectations, and relevant interview topics for the candidate's chosen domain.
*   **Strategist Agent**: Manages the live interview logic. It reviews session history to select the most relevant next question, manages topic transitions, and adjusts difficulty dynamically.
*   **Evaluator Agent**: Performs real-time analysis of candidate responses. It scores answers on technical accuracy, reasoning depth, and clarity, providing the feedback used to tune the interview strategy.
*   **Coach Agent**: Triggered at the end of the session to synthesize the full interview history into an actionable performance report.

### Orchestration Workflow
The system moves through four distinct states:
1.  **Intake**: Capturing user context and experience data.
2.  **Context Building**: Running Profile and Grounding agents to set the interview baseline.
3.  **Interview Loop**: Alternating between questioning (Strategist), transcription (STT), and evaluation (Evaluator).
4.  **Finalization**: Generating the final coach's report and archiving session data.

### Design Decisions and Tradeoffs

*   **Task Specialization**: Breaking the simulation into independent agents increases reliability and allows for modular debugging of complex behaviors like grading or strategic planning.
*   **Latency vs. Accuracy**: Integrating high-accuracy transcription (AssemblyAI) with multiple LLM calls adds some latency. The system uses a responsive UI architecture to manage these transitions smoothly.
*   **Privacy-First Persistence**: All session states, resumes, and transcripts are stored locally. This prioritizes data privacy and allows for offline review of reports once a session is complete.
*   **Structural Integrity**: Using a hard-coded state machine for orchestration ensures the interview remains goal-oriented and prevents the "drifting" often seen in purely chat-based AI simulations.

## Key Features
*   **Intake Profile Builder**: Seamlessly capture your target role and focus areas. Upload your resume (PDF) to ground the interview in your actual experience.
*   **Adaptive Interview Room**:
    *   **Live Webcam Preview**: Stay focused and maintain professional posture with a live camera feed.
    *   **Interactive Chatbot**: Engages you in a realistic dialogue with follow-up questions.
    *   **Dual Input Modes**: Respond using your microphone or type your answers manually.
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
    *   `GEMINI_API_KEY`: Get from [Google AI Studio](https://aistudio.google.com)
    *   `ASSEMBLYAI_API_KEY`: Get from [AssemblyAI](https://www.assemblyai.com)
    *   `FIRECRAWL_API_KEY`: Get from [FireCrawl](https://www.firecrawl.dev)
    *   `OPENROUTER_API_KEY`: Get from [OpenRouter](https://openrouter.ai)
    *   `GROQ_API_KEY`: Get from [Groq](https://groq.com)

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

## Interview Samples
All session transcripts, metrics, and generated reports are saved locally in the [data/sessions](./data/sessions) directory.