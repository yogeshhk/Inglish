"""
Document loader — extracts plain text from various input sources.

Supported sources:
  - Plain text string (direct passthrough)
  - PDF file (via pypdf)
  - DOCX file (via python-docx)
  - Uploaded Streamlit UploadedFile objects (auto-detected by filename extension)

Usage:
    from podgen.document_loader import DocumentLoader

    text = DocumentLoader.load_text("plain text here")
    text = DocumentLoader.load_file("/path/to/doc.pdf")
    text = DocumentLoader.load_uploaded(uploaded_file)  # Streamlit UploadedFile
"""

import io
import logging
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)


class DocumentLoader:
    """Extract plain text from text, PDF, or DOCX sources."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def load_text(text: str) -> str:
        """Return plain text as-is after normalising whitespace."""
        return _normalise(text)

    @staticmethod
    def load_file(path: Union[str, Path]) -> str:
        """
        Load and extract text from a file on disk.

        Detects format from file extension (.pdf / .docx / everything else → plain text).
        """
        path = Path(path)
        ext = path.suffix.lower()
        if ext == ".pdf":
            return DocumentLoader._extract_pdf_path(path)
        if ext in (".docx", ".doc"):
            return DocumentLoader._extract_docx_path(path)
        # Treat everything else as plain text
        return _normalise(path.read_text(encoding="utf-8", errors="replace"))

    @staticmethod
    def load_uploaded(uploaded_file) -> str:
        """
        Load text from a Streamlit UploadedFile object.

        Detects format from the file's `.name` attribute.
        """
        name = getattr(uploaded_file, "name", "") or ""
        ext = Path(name).suffix.lower()
        raw_bytes: bytes = uploaded_file.read()

        if ext == ".pdf":
            return DocumentLoader._extract_pdf_bytes(raw_bytes)
        if ext in (".docx", ".doc"):
            return DocumentLoader._extract_docx_bytes(raw_bytes)
        # Plain text / unknown
        return _normalise(raw_bytes.decode("utf-8", errors="replace"))

    # ------------------------------------------------------------------
    # PDF extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_pdf_path(path: Path) -> str:
        raw_bytes = path.read_bytes()
        return DocumentLoader._extract_pdf_bytes(raw_bytes)

    @staticmethod
    def _extract_pdf_bytes(data: bytes) -> str:
        try:
            from pypdf import PdfReader  # type: ignore
        except ImportError:
            raise ImportError(
                "pypdf is required for PDF support. Install with: pip install pypdf"
            )
        reader = PdfReader(io.BytesIO(data))
        pages = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            pages.append(page_text)
        return _normalise("\n".join(pages))

    # ------------------------------------------------------------------
    # DOCX extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_docx_path(path: Path) -> str:
        raw_bytes = path.read_bytes()
        return DocumentLoader._extract_docx_bytes(raw_bytes)

    @staticmethod
    def _extract_docx_bytes(data: bytes) -> str:
        try:
            import docx  # type: ignore  (python-docx)
        except ImportError:
            raise ImportError(
                "python-docx is required for DOCX support. Install with: pip install python-docx"
            )
        doc = docx.Document(io.BytesIO(data))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return _normalise("\n".join(paragraphs))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalise(text: str) -> str:
    """Collapse excessive blank lines and strip surrounding whitespace."""
    import re
    # Collapse 3+ consecutive newlines → double newline (paragraph break)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()
