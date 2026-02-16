"""
MSP Extractor Configuration
All thresholds and settings in one place
"""

class Config:
    """Global configuration with documented thresholds."""

    # === Value Bounds ===
    MAX_DISTANCE_METERS = 10000          # 10 km max (realistic for MSP)
    MAX_DISTANCE_KM = 500
    MAX_DISTANCE_NM = 200
    MAX_AREA_HECTARES = 10_000_000
    MAX_PENALTY_TL = 100_000_000_000
    MAX_PENALTY_EUR = 10_000_000_000

    # === Confidence Thresholds ===
    MIN_CONFIDENCE = 0.25
    MEDIUM_CONFIDENCE = 0.50
    HIGH_CONFIDENCE = 0.70

    # === Text Processing ===
    CONTEXT_WINDOW = 500
    MIN_SENTENCE_LENGTH = 15
    MAX_SENTENCE_LENGTH = 2500

    # === Marine Relevance Thresholds ===
    MARINE_RELEVANCE_LEGAL = 0.05        # Lower for legal docs
    MARINE_RELEVANCE_SCIENTIFIC = 0.15   # Higher for scientific papers

    # === Deduplication ===
    HASH_PREFIX_LENGTH = 16
