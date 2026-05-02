import gradio as gr
import uuid
import os
import PyPDF2
import re
from core.orchestrator import InterviewOrchestrator
from media.stt import STTManager

# In-memory session store for UI
sessions = {}
stt_manager = STTManager()

def get_orchestrator(session_id):
    if session_id not in sessions:
        sessions[session_id] = InterviewOrchestrator(session_id)
    return sessions[session_id]

def parse_resume(file_path):
    if not file_path:
        return "", ""
    text = ""
    links = []
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                    
        # Extract links (basic regex for linkedin/github)
        linkedin_matches = re.findall(r'(https?://[www\.]*linkedin\.com/in/[a-zA-Z0-9_-]+)', text)
        github_matches = re.findall(r'(https?://[www\.]*github\.com/[a-zA-Z0-9_-]+)', text)
        links.extend(linkedin_matches)
        links.extend(github_matches)
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        
    url_summaries = "\n".join(list(set(links)))
    return text, url_summaries

custom_css = """
.container { max-width: 1400px; margin: auto; }
.chat-window { border-radius: 10px; border: 1px solid #e5e7eb; background: #ffffff; padding: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
.section-card { border-radius: 12px; background: #f9fafb; padding: 15px; margin-bottom: 15px; border: 1px solid #e5e7eb; height: 100%; overflow-y: auto; max-height: 80vh; }
"""

def create_ui():
    with gr.Blocks(title="AI Interview Coach") as demo:
        gr.Markdown("# 🎓 AI Mock Interview Coach")
        session_id_state = gr.State(value="")
        
        with gr.Row():
            # COLUMN 1: Intake & Context
            with gr.Column(scale=1, elem_classes=["section-card"]):
                gr.Markdown("### 1. Intake Profile")
                role_in = gr.Textbox(label="Target Role", placeholder="e.g. Senior Backend Engineer")
                focus_in = gr.Textbox(label="Focus Area", placeholder="e.g. System Design, Python")
                resume_file = gr.File(label="Upload Resume (PDF)", file_types=[".pdf"], type="filepath")
                start_btn = gr.Button("🚀 Start Interview", variant="primary")
                
                gr.Markdown("### Candidate Profile")
                profile_out = gr.JSON(label="Auto-Generated Profile")
                
            # COLUMN 2: Interview Room
            with gr.Column(scale=2, elem_classes=["section-card"]):
                gr.Markdown("### 2. Interview Room")
                # Purely for realism, no backend logic attached to submit
                _ = gr.Image(sources=["webcam"], label="WebCam", interactive=True, height=200)
                
                chat_history = gr.Chatbot(label="Interview Chat", height=450, elem_classes=["chat-window"])
                
                gr.Markdown("#### Answer")
                with gr.Row():
                    audio_in = gr.Audio(sources=["microphone"], type="filepath", label="Voice Answer (Primary)")
                with gr.Row():
                    text_in = gr.Textbox(label="Text Answer (Fallback)", placeholder="Type your answer if microphone doesn't work...")
                    
                submit_btn = gr.Button("🎙️ Submit Answer", variant="primary")
                
            # COLUMN 3: Coaching & Feedback
            with gr.Column(scale=1, elem_classes=["section-card"]):
                gr.Markdown("### 3. Coaching & Evaluation")
                topic_out = gr.Textbox(label="Current Topic & Difficulty", interactive=False)
                eval_out = gr.JSON(label="Last Evaluation (Hidden in real life)")
                finish_btn = gr.Button("🏁 Finish Interview & Generate Report", variant="stop")
                
        # Additional row for the final report to take up full width
        with gr.Row():
            report_out = gr.Markdown(label="Final Coaching Report")
                
        def on_start(role, focus, resume_path):
            if not role or not focus:
                return "", [{"role": "assistant", "content": "Please provide at least a Role and Focus Area."}], {}, ""
                
            resume_text, url_summaries = parse_resume(resume_path)
                
            sess_id = str(uuid.uuid4())
            orch = get_orchestrator(sess_id)
            orch.process_intake(role, focus, resume_text, url_summaries, "")
            first_q = orch.start_interview()
            
            chat_val = [{"role": "assistant", "content": first_q}]
            prof_val = orch.state.candidate_profile.model_dump() if orch.state.candidate_profile else {}
            topic_val = f"Topic: {orch.state.current_topic} | Difficulty: {orch.state.difficulty_level}"
            
            return sess_id, chat_val, prof_val, topic_val

        start_btn.click(
            on_start,
            inputs=[role_in, focus_in, resume_file],
            outputs=[session_id_state, chat_history, profile_out, topic_out]
        )
        
        def on_submit(sess_id, history, audio_path, text_val):
            if not sess_id:
                history.append({"role": "assistant", "content": "Please start the interview first by filling out the Intake form."})
                return history, {}, "", None, ""
                
            orch = get_orchestrator(sess_id)
            
            transcript = ""
            if audio_path:
                transcript = stt_manager.transcribe_file_assemblyai(audio_path)
            elif text_val:
                transcript = text_val
                
            if not transcript:
                history.append({"role": "assistant", "content": "Error: No input."})
                return history, {}, "Error: No input.", None, ""
                
            next_q = orch.handle_answer(transcript, transcript)
            history.append({"role": "user", "content": transcript})
            history.append({"role": "assistant", "content": next_q})
            
            last_turn = orch.state.turn_history[-2] if len(orch.state.turn_history) > 1 else orch.state.turn_history[-1]
            eval_val = last_turn.evaluator_json.model_dump() if last_turn.evaluator_json else {}
            topic_val = f"Topic: {orch.state.current_topic} | Difficulty: {orch.state.difficulty_level}"
            
            return history, eval_val, topic_val, None, ""

        submit_btn.click(
            on_submit,
            inputs=[session_id_state, chat_history, audio_in, text_in],
            outputs=[chat_history, eval_out, topic_out, audio_in, text_in]
        )
        
        def on_finish(sess_id):
            if not sess_id:
                return "No active session."
            orch = get_orchestrator(sess_id)
            msg = orch._finish_interview()
            
            if orch.state.final_report_path and os.path.exists(orch.state.final_report_path):
                with open(orch.state.final_report_path, "r", encoding="utf-8") as f:
                    return f.read()
            return msg

        finish_btn.click(
            on_finish,
            inputs=[session_id_state],
            outputs=[report_out]
        )

    return demo.launch(css=custom_css)
