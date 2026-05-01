import os
import PyPDF2
import docx
import logging

logger = logging.getLogger(__name__)

class ResumeParser:
    @staticmethod
    def parse(file_path: str) -> str:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return ""
            
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == '.pdf':
                return ResumeParser._parse_pdf(file_path)
            elif ext == '.docx':
                return ResumeParser._parse_docx(file_path)
            elif ext == '.txt':
                return ResumeParser._parse_txt(file_path)
            else:
                logger.warning(f"Unsupported file extension: {ext}")
                return ""
        except Exception as e:
            logger.error(f"Error parsing resume {file_path}: {e}")
            return ""

    @staticmethod
    def _parse_pdf(file_path: str) -> str:
        text = ""
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        return text.strip()

    @staticmethod
    def _parse_docx(file_path: str) -> str:
        doc = docx.Document(file_path)
        text = [para.text for para in doc.paragraphs if para.text]
        return "\n".join(text).strip()

    @staticmethod
    def _parse_txt(file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read().strip()
