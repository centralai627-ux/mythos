"""
Mythos Vision
=============
Handles image & file loading, base64 encoding, and routing to the
vision model. Supports PNG/JPG/GIF/WEBP and document-like files.
"""
from __future__ import annotations
import base64
import mimetypes
import os
from typing import Optional, Tuple

from .api_client import MythosAPI, APIError


# Supported image MIME types.
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}

# Map common doc extensions to a friendly label (we still send as image-like
# data URL; the vision model handles text-rich images well).
DOC_EXTS = {".pdf", ".txt", ".md", ".csv", ".json", ".html", ".htm",
            ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt"}


class MythosVision:
    """Vision/file analyzer."""

    MAX_BYTES = 8_000_000  # 8 MB guard.

    def __init__(self, api: MythosAPI) -> None:
        self.api = api

    def analyze_file(self, path: str, question: str = "Describe this in detail.") -> str:
        """Load a file and send it to Mythos-Vision for analysis."""
        if not os.path.isfile(path):
            return f"⚠ File not found: {path}"

        size = os.path.getsize(path)
        if size > self.MAX_BYTES:
            return (f"⚠ File too large ({size:,} bytes). "
                    f"Max {self.MAX_BYTES:,} bytes.")

        ext = os.path.splitext(path)[1].lower()
        if ext in IMAGE_EXTS:
            return self._analyze_image(path, question)
        if ext in DOC_EXTS:
            # For text docs, read & pass as text to vision-capable model.
            return self._analyze_text_file(path, question)
        return (f"⚠ Unsupported file type: {ext}. "
                f"Supported: {', '.join(sorted(IMAGE_EXTS | DOC_EXTS))}")

    def _analyze_image(self, path: str, question: str) -> str:
        try:
            with open(path, "rb") as f:
                raw = f.read()
        except OSError as e:
            return f"⚠ Cannot read file: {e}"

        b64 = base64.b64encode(raw).decode("ascii")
        mime = mimetypes.guess_type(path)[0] or "image/png"

        prompt = (
            f"{question}\n\n"
            "Analyze this image precisely. If it contains UI/code/layout, "
            "describe structure, colors, components. If asked to reproduce, "
            "emit clean code."
        )
        try:
            return self.api.vision(prompt, image_base64=b64, mime=mime)
        except APIError as e:
            return f"⚠ Vision error: {e}"

    def _analyze_text_file(self, path: str, question: str) -> str:
        try:
            ext = os.path.splitext(path)[1].lower()
            
            # Handle .docx files
            if ext == ".docx":
                content = self._extract_docx_text(path)
            else:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read(200_000)  # cap at 200k chars
        except OSError as e:
            return f"⚠ Cannot read file: {e}"

        prompt = (
            f"Analyze this file ({os.path.basename(path)}):\n\n"
            f"```\n{content}\n```\n\nQuestion: {question}"
        )
        try:
            return self.api.chat(
                [{"role": "user", "content": prompt}],
                model_alias="mythos-vision",
                max_tokens=2048,
            )
        except APIError as e:
            return f"⚠ Vision error: {e}"
    
    def _extract_docx_text(self, path: str) -> str:
        """Extract text from .docx file."""
        try:
            from docx import Document
            doc = Document(path)
            text_parts = []
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)
            return "\n".join(text_parts)[:200_000]
        except ImportError:
            return "⚠ python-docx not installed. Run: pip install python-docx"
        except Exception as e:
            return f"⚠ Cannot read .docx: {e}"
