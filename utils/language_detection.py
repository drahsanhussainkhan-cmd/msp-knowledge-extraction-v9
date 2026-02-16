#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Language and document type detection for MSP documents.
Extracted from msp_extractor_v8_complete.
"""

try:
    from ..core.enums import DocumentType
except ImportError:
    from core.enums import DocumentType


# Threshold for Turkish character detection
TURKISH_CHAR_THRESHOLD = 0.02


class LanguageDetector:
    """
    Detect document language and type.

    Uses character analysis and keyword matching to classify documents.
    """

    TURKISH_CHARS = set('çÇğĞıİöÖşŞüÜ')

    LEGAL_TURKISH_KEYWORDS = [
        'kanun', 'yönetmelik', 'tebliğ', 'madde', 'fıkra', 'bent',
        'resmi gazete', 'sayılı', 'tarihli', 'hüküm', 'yasak',
        'müeyyide', 'ceza', 'idari para cezası'
    ]

    LEGAL_ENGLISH_KEYWORDS = [
        'directive', 'regulation', 'article', 'section', 'paragraph',
        'pursuant to', 'hereby', 'shall', 'whereas', 'enacted',
        'statutory', 'legislation', 'provision'
    ]

    SCIENTIFIC_ENGLISH_KEYWORDS = [
        'abstract', 'introduction', 'methodology', 'results', 'discussion',
        'conclusion', 'references', 'et al', 'study', 'research',
        'findings', 'analysis', 'hypothesis', 'significant', 'p-value'
    ]

    SCIENTIFIC_TURKISH_KEYWORDS = [
        'özet', 'giriş', 'yöntem', 'bulgular', 'sonuç', 'tartışma',
        'kaynaklar', 'çalışma', 'araştırma', 'analiz', 'hipotez'
    ]

    @classmethod
    def detect(cls, text: str) -> DocumentType:
        """
        Detect document type and language.

        Args:
            text: Document text (first 5000 chars used)

        Returns:
            DocumentType enum value
        """
        if not text:
            return DocumentType.UNKNOWN

        text_sample = text[:5000]
        text_lower = text_sample.lower()

        # Check Turkish character ratio
        turkish_chars = sum(1 for c in text_sample if c in cls.TURKISH_CHARS)
        turkish_ratio = turkish_chars / len(text_sample) if text_sample else 0
        is_turkish = turkish_ratio > TURKISH_CHAR_THRESHOLD

        # Count keyword matches
        legal_tr = sum(1 for kw in cls.LEGAL_TURKISH_KEYWORDS if kw in text_lower)
        legal_en = sum(1 for kw in cls.LEGAL_ENGLISH_KEYWORDS if kw in text_lower)
        sci_en = sum(1 for kw in cls.SCIENTIFIC_ENGLISH_KEYWORDS if kw in text_lower)
        sci_tr = sum(1 for kw in cls.SCIENTIFIC_TURKISH_KEYWORDS if kw in text_lower)

        # Determine type
        if is_turkish:
            if legal_tr >= sci_tr:
                return DocumentType.LEGAL_TURKISH
            return DocumentType.SCIENTIFIC_TURKISH
        else:
            if legal_en >= sci_en:
                return DocumentType.LEGAL_ENGLISH
            return DocumentType.SCIENTIFIC_ENGLISH

    @classmethod
    def get_language(cls, doc_type: DocumentType) -> str:
        """Get language string from document type."""
        if doc_type in [DocumentType.LEGAL_TURKISH, DocumentType.SCIENTIFIC_TURKISH]:
            return "turkish"
        return "english"

    @classmethod
    def is_legal(cls, doc_type: DocumentType) -> bool:
        """Check if document is legal type."""
        return doc_type in [DocumentType.LEGAL_TURKISH, DocumentType.LEGAL_ENGLISH]

    @classmethod
    def is_scientific(cls, doc_type: DocumentType) -> bool:
        """Check if document is scientific type."""
        return doc_type in [DocumentType.SCIENTIFIC_ENGLISH, DocumentType.SCIENTIFIC_TURKISH]
