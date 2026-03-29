import fitz  # PyMuPDF
import pdfplumber
import os

def extract_text_from_pdf(file_path: str) -> str:
    """Extract all text from a PDF file"""
    text = ""

    # Try pdfplumber first (better for structured CVs)
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        if text.strip():
            return text.strip()
    except Exception:
        pass

    # Fallback to PyMuPDF
    try:
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
    except Exception as e:
        return f"Error extracting text: {str(e)}"

    return text.strip()


def extract_cv_sections(raw_text: str) -> dict:
    """Ask the structure out of raw CV text"""
    sections = {
        "raw_text": raw_text,
        "word_count": len(raw_text.split()),
        "has_education": any(word in raw_text.lower() for word in ["education", "university", "degree", "bachelor", "master", "phd"]),
        "has_experience": any(word in raw_text.lower() for word in ["experience", "worked", "position", "role", "job"]),
        "has_skills": any(word in raw_text.lower() for word in ["skills", "technologies", "tools", "languages"]),
    }
    return sections