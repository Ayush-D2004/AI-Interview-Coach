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
        linkedin_matches = re.findall(r'(https?://[www\.]*linkedin\.com/in/[a-zA-Z0-9_\-]+)', text)
        github_matches   = re.findall(r'(https?://[www\.]*github\.com/[a-zA-Z0-9_\-]+)', text)
        links.extend(linkedin_matches)
        links.extend(github_matches)
    except Exception as e:
        print(f"Error parsing PDF: {e}")
    url_summaries = "\n".join(list(set(links)))
    return text, url_summaries

# ── CSS ────────────────────────────────────────────────────────────────────────
custom_css = """
/* Full-height root */
html, body, .gradio-container { height: 100%; margin: 0; padding: 0; }
.full-height-row { min-height: calc(100vh - 120px); }

/* Section cards */
.section-card {
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    padding: 16px;
    height: calc(100vh - 140px);
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

/* Chat window */
.chat-window {
    flex: 1 1 auto;
    border-radius: 10px;
    border: 1px solid #e5e7eb;
    background: #ffffff;
    padding: 10px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}

/* Report typography */
.report-area {
    font-size: 15px !important;
    line-height: 1.7 !important;
    padding: 24px !important;
    border-radius: 10px;
    border: 1px solid #e5e7eb;
    background: #fafafa;
}
.report-area h1 { font-size: 22px !important; margin-bottom: 12px !important; }
.report-area h2 { font-size: 18px !important; margin-bottom: 8px !important; }
.report-area h3 { font-size: 16px !important; margin-bottom: 6px !important; }
.report-area p, .report-area li { font-size: 15px !important; }

/* Collapsible eval button */
.eval-toggle-btn {
    margin-left: auto;
    font-size: 11px !important;
    padding: 2px 8px !important;
    border-radius: 6px !important;
}
"""

def create_ui():
    with gr.Blocks(title="AI Interview Coach") as demo:
        gr.Markdown("# 🎓 AI Mock Interview Coach")
        session_id_state = gr.State(value="")

        with gr.Row(elem_classes=["full-height-row"]):

            # ── COLUMN 1 : Intake & Context ────────────────────────────────
            with gr.Column(scale=1, elem_classes=["section-card"]):
                gr.Markdown("### 1. Intake Profile")
                role_in  = gr.Textbox(label="Target Role",  placeholder="e.g. Senior Backend Engineer")
                focus_in = gr.Textbox(label="Focus Area",   placeholder="e.g. System Design, Python")
                resume_file = gr.File(
                    label="Upload Resume (PDF)",
                    file_types=[".pdf"],
                    type="filepath"
                )
                start_btn = gr.Button("🚀 Start Interview", variant="primary")


            # ── COLUMN 2 : Interview Room ──────────────────────────────────
            with gr.Column(scale=2, elem_classes=["section-card"]):
                gr.Markdown("### 2. Interview Room")

                # Large webcam
                _ = gr.Image(
                    sources=["webcam"],
                    label="Camera Preview",
                    interactive=True,
                    height=300,
                )

                # Chat takes remaining vertical space
                chat_history = gr.Chatbot(
                    label="Interview Chat",
                    height=250,
                    elem_classes=["chat-window"],
                )

                gr.Markdown("#### Your Answer")

                # Answer inputs stacked vertically — no horizontal scroll
                audio_in = gr.Audio(
                    sources=["microphone"],
                    type="filepath",
                    label="Voice Answer",
                )
                with gr.Group():
                    with gr.Row():
                        gr.Markdown("#### Text Answer")
                        with gr.Column(scale=0, min_width=150):
                            submit_btn = gr.Button("Submit Answer ➤", variant="primary", size="sm")
                    text_in = gr.Textbox(
                        show_label=False,
                        placeholder="Type your answer here if microphone isn't available…",
                        lines=3,
                    )

            # ── COLUMN 3 : Coaching & Evaluation ──────────────────────────
            with gr.Column(scale=1, elem_classes=["section-card"]):
                gr.Markdown("### 3. Coaching & Evaluation")

                topic_out = gr.Textbox(
                    label="Current Topic & Difficulty",
                    interactive=False,
                )

                # Toggle button + collapsible JSON panel
                with gr.Row():
                    gr.Markdown("**AI Evaluation**")
                    toggle_eval_btn = gr.Button(
                        "Show/Hide ",
                        size="sm",
                        elem_classes=["eval-toggle-btn"],
                    )

                eval_out = gr.JSON(
                    label="Evaluation Detail",
                    visible=False,
                )

                # Push finish button to bottom with a spacer
                gr.HTML("<div style='flex:1'></div>")
                finish_btn = gr.Button(
                    "Finish Interview & Generate Report",
                    variant="stop",
                )

        # ── Report row (full-width, below the 3-column section) ───────────
        with gr.Row():
            report_out = gr.Markdown(
                value="",
                label="Final Coaching Report",
                elem_classes=["report-area"],
            )

        # ── Event handlers ────────────────────────────────────────────────
        def on_start(role, focus, resume_path):
            if not role or not focus:
                return (
                    "",
                    [{"role": "assistant", "content": "⚠️ Please provide at least a Role and Focus Area."}],
                    {},
                    "",
                )
            resume_text, url_summaries = parse_resume(resume_path)
            sess_id = str(uuid.uuid4())
            orch = get_orchestrator(sess_id)
            orch.process_intake(role, focus, resume_text, url_summaries, "")
            first_q   = orch.start_interview()
            chat_val  = [{"role": "assistant", "content": first_q}]
            prof_val  = orch.state.candidate_profile.model_dump() if orch.state.candidate_profile else {}
            topic_val = f"Topic: {orch.state.current_topic} | Difficulty: {orch.state.difficulty_level}"
            return sess_id, chat_val, topic_val

        start_btn.click(
            on_start,
            inputs=[role_in, focus_in, resume_file],
            outputs=[session_id_state, chat_history, topic_out],
        )

        def on_submit(sess_id, history, audio_path, text_val):
            if not sess_id:
                history.append({"role": "assistant", "content": "⚠️ Please start the interview first."})
                return history, {}, "", None, ""
            orch = get_orchestrator(sess_id)
            transcript = ""
            if audio_path:
                transcript = stt_manager.transcribe_file_assemblyai(audio_path)
            elif text_val:
                transcript = text_val
            if not transcript:
                history.append({"role": "assistant", "content": "⚠️ No input detected — please speak or type an answer."})
                return history, {}, "", None, ""
            next_q = orch.handle_answer(transcript, transcript)
            history.append({"role": "user",      "content": transcript})
            history.append({"role": "assistant", "content": next_q})
            last_turn = (
                orch.state.turn_history[-2]
                if len(orch.state.turn_history) > 1
                else orch.state.turn_history[-1]
            )
            eval_val  = last_turn.evaluator_json.model_dump() if last_turn.evaluator_json else {}
            topic_val = f"Topic: {orch.state.current_topic} | Difficulty: {orch.state.difficulty_level}"
            return history, eval_val, topic_val, None, ""

        submit_btn.click(
            on_submit,
            inputs=[session_id_state, chat_history, audio_in, text_in],
            outputs=[chat_history, eval_out, topic_out, audio_in, text_in],
        )

        # Toggle eval JSON visibility
        def toggle_eval(visible):
            return gr.update(visible=not visible), not visible

        eval_visible_state = gr.State(value=False)
        toggle_eval_btn.click(
            toggle_eval,
            inputs=[eval_visible_state],
            outputs=[eval_out, eval_visible_state],
        )

        def on_finish(sess_id):
            if not sess_id:
                return "No active session."
            orch = get_orchestrator(sess_id)
            msg  = orch._finish_interview()
            if orch.state.final_report_path and os.path.exists(orch.state.final_report_path):
                with open(orch.state.final_report_path, "r", encoding="utf-8") as f:
                    return f.read()
            return msg

        finish_btn.click(
            on_finish,
            inputs=[session_id_state],
            outputs=[report_out],
        )

    return demo
