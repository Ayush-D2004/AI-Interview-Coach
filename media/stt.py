import os
import logging
import assemblyai as aai
from faster_whisper import WhisperModel
from typing import Optional, Callable

logger = logging.getLogger(__name__)

class STTManager:
    def __init__(self, fallback_model_size="base"):
        self.aai_api_key = os.environ.get("ASSEMBLYAI_API_KEY")
        if self.aai_api_key:
            aai.settings.api_key = self.aai_api_key
        else:
            logger.warning("ASSEMBLYAI_API_KEY not found. Will use faster-whisper fallback exclusively.")

        self.fallback_model_size = fallback_model_size
        self.whisper_model = None  # Lazy load

    def _load_whisper(self):
        if self.whisper_model is None:
            logger.info("Loading faster-whisper model...")
            self.whisper_model = WhisperModel(self.fallback_model_size, device="cpu", compute_type="int8")

    def transcribe_file_fallback(self, file_path: str) -> str:
        """Fallback to faster-whisper for a complete file."""
        self._load_whisper()
        segments, info = self.whisper_model.transcribe(file_path, beam_size=5)
        text = " ".join([segment.text for segment in segments])
        return text.strip()
        
    def transcribe_file_assemblyai(self, file_path: str) -> str:
        """Use AssemblyAI synchronous API as another option for whole files."""
        if not self.aai_api_key:
            return self.transcribe_file_fallback(file_path)
            
        try:
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(file_path)
            if transcript.status == aai.TranscriptStatus.error:
                logger.error(f"AssemblyAI Error: {transcript.error}")
                return self.transcribe_file_fallback(file_path)
            return transcript.text
        except Exception as e:
            logger.error(f"AssemblyAI Exception: {e}")
            return self.transcribe_file_fallback(file_path)

    def get_realtime_transcriber(self, 
                                 on_data: Callable[[aai.RealtimeTranscript], None],
                                 on_error: Callable[[aai.RealtimeError], None],
                                 on_open: Callable[[aai.RealtimeSessionOpened], None],
                                 on_close: Callable[[], None]) -> Optional[aai.RealtimeTranscriber]:
        """Returns a configured AssemblyAI RealtimeTranscriber for streaming."""
        if not self.aai_api_key:
            return None
            
        transcriber = aai.RealtimeTranscriber(
            on_data=on_data,
            on_error=on_error,
            sample_rate=16000,
            on_open=on_open,
            on_close=on_close,
        )
        return transcriber
