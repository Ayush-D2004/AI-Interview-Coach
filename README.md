# AI Mock Interview Coach

## Project Overview
The AI Mock Interview Coach is a production-grade application designed to provide structured, adaptive, and realistic interview simulations. The system employs a multi-agent architecture to handle candidate intake, interview planning, real-time speech-to-text processing, answer evaluation, and comprehensive coaching feedback. Unlike generic chatbots, this system follows a deterministic state machine to ensure a professional and goal-oriented interview experience.

## Core Functionalities
- Multi-Agent Orchestration: Utilizing distinct agents for profile building, interview strategy, answer evaluation, and final coaching.
- Adaptive Interviewing: The system adjusts question difficulty (Easy, Medium, Hard, Expert) and topics dynamically based on the candidate's performance.
- Speech-to-Text Integration: Primary input via microphone using AssemblyAI for transcription, with a local fallback to faster-whisper.
- Automated Evaluation: Structured scoring across multiple dimensions including correctness, specificity, reasoning, clarity, and communication.
- Final Coaching Report: Generates a detailed Markdown report at the conclusion of the session, highlighting strengths and areas for improvement.
- Web-Based Dashboard: A 3-column Gradio interface providing a seamless user experience from intake to feedback.

## Tech Stack
- Frontend: Gradio
- Language: Python 3.10+
- AI Models: Google Gemini (Flash and Pro), Groq (Llama-3), and OpenRouter.
- Speech-to-Text: AssemblyAI (Real-time and Sync API), faster-whisper (Local).
- Data Validation: Pydantic v2.
- Grounding: Firecrawl API for real-time role and industry expectations.
- Documentation & Reporting: Markdown.

## Installation and Setup

### Prerequisites
- Python 3.10 or higher.
- A virtual environment is highly recommended.

### Configuration
1. Clone the repository to your local machine.
2. Create a .env file in the root directory. You can use the .env.example file as a template.
3. Obtain and enter the following API keys:
   - GEMINI_API_KEY: For primary LLM functionality.
   - ASSEMBLYAI_API_KEY: For speech-to-text processing.
   - FIRECRAWL_API_KEY: For real-time grounding search.
   - GROQ_API_KEY: For fallback LLM performance.
   - OPENROUTER_API_KEY: For additional model fallbacks.

### Installation Steps
1. Navigate to the project root directory.
2. Install the required dependencies using pip:
   pip install -r requirements.txt

## Running the Application
To launch the AI Mock Interview Coach, execute the following command in your terminal:

python app.py

Once the server initializes, the terminal will display a local URL (typically http://127.0.0.1:7860). Open this address in your web browser to access the dashboard.

## System Architecture
The application operates as a state machine with the following phases:
1. INTAKE: Gathers candidate background and target role details.
2. PROFILE_BUILD: Generates a structured candidate profile using the Profile Agent.
3. INTERVIEW_PLAN: Formulates an initial strategy based on the profile and industry benchmarks.
4. ASK_QUESTION: Presents questions to the candidate.
5. EVALUATE_ANSWER: Analyzes candidate responses using the Evaluator Agent.
6. DECIDE_NEXT_STEP: The Strategist Agent determines whether to continue, adjust difficulty, or conclude the session.
7. COACH: The Coach Agent generates the final performance review.
8. FINAL_REPORT: Produces the persistent coaching document.

## Data Persistence
All session data, including transcripts, evaluator outputs, and metrics, are stored locally in the data/sessions directory. Each session is assigned a unique identifier for traceability and offline review.
