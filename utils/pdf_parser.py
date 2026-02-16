#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF text extraction utilities for MSP documents.
"""

from typing import Dict, Tuple, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger.warning("pdfplumber not available. Install: pip install pdfplumber")


def extract_text_from_pdf(pdf_path: str) -> Tuple[str, Dict[int, str]]:
    """
    Extract full text and page-by-page text from a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Tuple of (full_text, page_texts_dict)
        where page_texts_dict maps page_number (1-indexed) -> page_text

    Raises:
        ImportError: If pdfplumber is not installed
        FileNotFoundError: If PDF file doesn't exist
    """
    if not PDFPLUMBER_AVAILABLE:
        raise ImportError(
            "pdfplumber is required for PDF extraction. "
            "Install it with: pip install pdfplumber"
        )

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    page_texts = {}
    full_text_parts = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            page_texts[i] = text
            full_text_parts.append(text)

    full_text = '\n\n'.join(full_text_parts)

    return full_text, page_texts


def get_pdf_metadata(pdf_path: str) -> Dict:
    """
    Extract metadata from a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Dict with metadata (title, author, pages, etc.)
    """
    if not PDFPLUMBER_AVAILABLE:
        raise ImportError("pdfplumber is required")

    pdf_path = Path(pdf_path)
    metadata = {
        'filename': pdf_path.name,
        'filepath': str(pdf_path),
        'pages': 0,
        'title': None,
        'author': None,
    }

    with pdfplumber.open(str(pdf_path)) as pdf:
        metadata['pages'] = len(pdf.pages)
        if pdf.metadata:
            metadata['title'] = pdf.metadata.get('Title')
            metadata['author'] = pdf.metadata.get('Author')

    return metadata
