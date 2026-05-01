import gradio as gr
import uuid
import os
from core.orchestrator import InterviewOrchestrator
from media.stt import STTManager

# In-memory session store for UI
sessions = {}
stt_manager = STTManager()

def get_orchestrator(session_id):
    if session_id not in sessions:
        sessions[session_id] = InterviewOrchestrator(session_id)
    return sessions[session_id]

def create_ui():
    theme = gr.themes.Soft(
        primary_hue="indigo",
        secondary_hue="blue",
    )
    
    with gr.Blocks(title="AI Interview Coach", theme=theme) as demo:
        gr.Markdown("# 🎓 AI Mock Interview Coach")
        session_id_state = gr.State(value="")
        
        with gr.Row():
            # COLUMN 1: Intake & Context
            with gr.Column(scale=1):
                gr.Markdown("### 1. Intake Profile")
                role_in = gr.Textbox(label="Target Role", placeholder="e.g. Senior Backend Engineer")
                focus_in = gr.Textbox(label="Focus Area", placeholder="e.g. System Design, Python")
                resume_in = gr.Textbox(label="Resume / Background", lines=8, placeholder="Paste your resume or background snippet here...")
                start_btn = gr.Button("🚀 Start Interview", variant="primary")
                
                gr.Markdown("### Candidate Profile")
                profile_out = gr.JSON(label="Auto-Generated Profile")
                
            # COLUMN 2: Interview Room
            with gr.Column(scale=2):
                gr.Markdown("### 2. Interview Room")
                # Purely for realism, no backend logic attached to submit
                _ = gr.Image(sources=["webcam"], label="Camera Preview (UI Only)", interactive=True)
                
                chat_history = gr.Chatbot(label="Interview Chat", height=450)
                
                gr.Markdown("#### Answer")
                with gr.Row():
                    audio_in = gr.Audio(sources=["microphone"], type="filepath", label="Voice Answer (Primary)")
                with gr.Row():
                    text_in = gr.Textbox(label="Text Answer (Fallback)", placeholder="Type your answer if microphone doesn't work...")
                    
                submit_btn = gr.Button("🎙️ Submit Answer")
                
            # COLUMN 3: Coaching & Feedback
            with gr.Column(scale=1):
                gr.Markdown("### 3. Coaching & Evaluation")
                topic_out = gr.Textbox(label="Current Topic & Difficulty", interactive=False)
                eval_out = gr.JSON(label="Last Evaluation (Hidden in real life)")
                finish_btn = gr.Button("🏁 Finish Interview & Generate Report", variant="stop")
                
        # Additional row for the final report to take up full width
        with gr.Row():
            report_out = gr.Markdown(label="Final Coaching Report")
                
        def on_start(role, focus, resume):
            if not role or not focus:
                return "", [(None, "Please provide at least a Role and Focus Area.")], {}, ""
                
            sess_id = str(uuid.uuid4())
            orch = get_orchestrator(sess_id)
            orch.process_intake(role, focus, resume, "", "")
            first_q = orch.start_interview()
            
            chat_val = [(None, first_q)]
            prof_val = orch.state.candidate_profile.model_dump() if orch.state.candidate_profile else {}
            topic_val = f"Topic: {orch.state.current_topic} | Difficulty: {orch.state.difficulty_level}"
            
            return sess_id, chat_val, prof_val, topic_val

        start_btn.click(
            on_start,
            inputs=[role_in, focus_in, resume_in],
            outputs=[session_id_state, chat_history, profile_out, topic_out]
        )
        
        def on_submit(sess_id, history, audio_path, text_val):
            if not sess_id:
                history.append((None, "Please start the interview first by filling out the Intake form."))
                return history, {}, "", None, ""
                
            orch = get_orchestrator(sess_id)
            
            transcript = ""
            if audio_path:
                transcript = stt_manager.transcribe_file_assemblyai(audio_path)
            elif text_val:
                transcript = text_val
                
            if not transcript:
                return history, {}, "Error: No input.", None, ""
                
            next_q = orch.handle_answer(transcript, transcript)
            history.append((transcript, next_q))
            
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

    return demo
