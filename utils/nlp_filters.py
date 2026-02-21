"""
Advanced NLP filters for extraction validation.

Implements classical NLP techniques to improve extraction precision:
1. Named Entity Recognition (NER) validation using NLTK
2. Part-of-Speech (POS) tag analysis for garble detection
3. Language coherence scoring (perplexity proxy)
4. Enhanced citation/bibliography pattern detection
5. TF-IDF category classifier (trained on annotated data)

These are all classical NLP - no LLM, no API calls, fully reproducible.
"""

import re
import math
import logging
from typing import Dict, List, Optional, Tuple
from collections import Counter
from pathlib import Path

logger = logging.getLogger(__name__)

# Lazy-load NLTK to avoid import overhead when not needed
_nltk_loaded = False
_nltk_tagger = None
_nltk_chunker = None
_nltk_tokenizer = None


def _ensure_nltk():
    """Lazy-load NLTK components."""
    global _nltk_loaded, _nltk_tagger, _nltk_chunker, _nltk_tokenizer
    if _nltk_loaded:
        return True
    try:
        import nltk
        # These should already be downloaded
        _nltk_tokenizer = nltk.word_tokenize
        _nltk_tagger = nltk.pos_tag
        _nltk_chunker = nltk.ne_chunk
        _nltk_loaded = True
        return True
    except Exception as e:
        logger.warning(f"NLTK not available: {e}")
        return False


# =============================================================================
# 1. NAMED ENTITY RECOGNITION (NER) VALIDATION
# =============================================================================

class NERValidator:
    """
    Use NLTK NER to validate extractions.

    For stakeholder/institution categories, the extracted text should
    contain recognized ORG/PERSON/GPE entities. If NLTK doesn't
    recognize any entities, the extraction is likely a false positive.
    """

    # Categories that should contain named entities
    ENTITY_CATEGORIES = {
        'stakeholder': ['ORGANIZATION', 'GPE', 'PERSON'],
        'institution': ['ORGANIZATION', 'GPE'],
        'species': [],       # Species won't be NER entities - use POS instead
        'policy': ['ORGANIZATION', 'GPE'],  # Policies often contain org/place names
    }

    # Known valid entities that NLTK might miss (domain-specific)
    KNOWN_ENTITIES = {
        'stakeholder': {
            'fishing industry', 'tourism sector', 'aquaculture sector',
            'local communities', 'indigenous peoples', 'fishermen', 'fishers',
            'port authority', 'tourism operators', 'shipping industry',
            'renewable energy sector', 'oil and gas sector', 'mining sector',
            'environmental groups', 'conservation organizations',
            'coastal communities', 'recreational users', 'divers',
        },
        'institution': {
            'european commission', 'helcom', 'ospar', 'ices', 'iucn',
            'unesco', 'imo', 'unep', 'fao', 'noaa', 'epa',
        },
    }

    def __init__(self):
        self._ready = _ensure_nltk()

    def validate(self, text: str, category: str) -> Tuple[bool, float, str]:
        """
        Validate extraction using NER.

        Args:
            text: The extracted text
            category: Extraction category

        Returns:
            Tuple of (is_valid, confidence_adjustment, reason)
            confidence_adjustment: multiplier (0.0-1.5) to adjust confidence
        """
        if not self._ready or category not in self.ENTITY_CATEGORIES:
            return True, 1.0, "ner_not_applicable"

        # Check known entities first (fast path)
        text_lower = text.lower().strip()
        known_set = self.KNOWN_ENTITIES.get(category, set())
        if any(known in text_lower for known in known_set):
            return True, 1.2, "known_entity_match"

        # Skip very short text (single words are often valid)
        if len(text.split()) <= 2:
            return True, 1.0, "too_short_for_ner"

        expected_types = self.ENTITY_CATEGORIES[category]
        if not expected_types:
            return True, 1.0, "no_entity_types_expected"

        try:
            tokens = _nltk_tokenizer(text)
            tagged = _nltk_tagger(tokens)
            chunks = _nltk_chunker(tagged)

            found_entities = []
            for chunk in chunks:
                if hasattr(chunk, 'label'):
                    found_entities.append(chunk.label())

            if not found_entities:
                # No entities found - likely false positive for entity categories
                # But don't reject outright - lower confidence
                return True, 0.5, "no_ner_entities_found"

            # Check if found entities match expected types
            matched = any(e in expected_types for e in found_entities)
            if matched:
                return True, 1.3, f"ner_confirmed({','.join(found_entities)})"
            else:
                # Found entities but wrong type
                return True, 0.7, f"ner_type_mismatch(found={','.join(found_entities)})"

        except Exception as e:
            logger.debug(f"NER validation error: {e}")
            return True, 1.0, "ner_error"


# =============================================================================
# 2. POS-BASED GARBLE DETECTION
# =============================================================================

class POSGarbleDetector:
    """
    Use Part-of-Speech tagging to detect garbled text.

    Garbled text from PDF column merging has abnormal POS patterns:
    - Random sequences of nouns without connective words
    - Unusual verb/adjective distributions
    - High ratio of proper nouns (title fragments mashed together)
    """

    # Normal English POS distribution (approximate)
    # NN/NNS: 25-35%, VB*: 10-20%, DT: 8-12%, IN: 10-15%, JJ: 5-10%
    GARBLE_THRESHOLDS = {
        'max_proper_noun_ratio': 0.60,   # >60% proper nouns = likely garbled
        'min_function_word_ratio': 0.05,  # <5% function words = likely garbled
        'max_consecutive_nouns': 6,       # 6+ nouns in a row = likely garbled
    }

    FUNCTION_POS = {'DT', 'IN', 'CC', 'TO', 'MD', 'WDT', 'WP', 'WRB', 'EX', 'RP'}
    NOUN_POS = {'NN', 'NNS', 'NNP', 'NNPS'}
    PROPER_NOUN_POS = {'NNP', 'NNPS'}

    def __init__(self):
        self._ready = _ensure_nltk()

    def is_garbled(self, text: str) -> Tuple[bool, str]:
        """
        Check if text is garbled using POS analysis.

        Args:
            text: Text to check

        Returns:
            Tuple of (is_garbled, reason)
        """
        if not self._ready or not text or len(text) < 20:
            return False, "too_short"

        try:
            tokens = _nltk_tokenizer(text)
            if len(tokens) < 5:
                return False, "too_few_tokens"

            tagged = _nltk_tagger(tokens)
            pos_tags = [tag for _, tag in tagged]
            total = len(pos_tags)

            # Check 1: Proper noun ratio
            proper_count = sum(1 for p in pos_tags if p in self.PROPER_NOUN_POS)
            proper_ratio = proper_count / total
            if proper_ratio > self.GARBLE_THRESHOLDS['max_proper_noun_ratio']:
                return True, f"high_proper_noun_ratio({proper_ratio:.2f})"

            # Check 2: Function word ratio
            function_count = sum(1 for p in pos_tags if p in self.FUNCTION_POS)
            function_ratio = function_count / total
            if function_ratio < self.GARBLE_THRESHOLDS['min_function_word_ratio'] and total > 10:
                return True, f"low_function_word_ratio({function_ratio:.2f})"

            # Check 3: Consecutive nouns
            max_consecutive = 0
            current_consecutive = 0
            for pos in pos_tags:
                if pos in self.NOUN_POS:
                    current_consecutive += 1
                    max_consecutive = max(max_consecutive, current_consecutive)
                else:
                    current_consecutive = 0

            if max_consecutive >= self.GARBLE_THRESHOLDS['max_consecutive_nouns']:
                return True, f"consecutive_nouns({max_consecutive})"

            return False, "pos_normal"

        except Exception as e:
            logger.debug(f"POS garble detection error: {e}")
            return False, "pos_error"


# =============================================================================
# 3. LANGUAGE COHERENCE SCORING (Perplexity Proxy)
# =============================================================================

class CoherenceScorer:
    """
    Score text coherence using character n-gram statistics.

    This is a lightweight perplexity proxy that doesn't require
    a trained language model. It uses character-level statistics
    to detect text that doesn't look like natural English or Turkish.

    Garbled text scores LOW (incoherent), natural text scores HIGH.
    """

    # Common English bigrams (top 50)
    ENGLISH_BIGRAMS = {
        'th', 'he', 'in', 'er', 'an', 'en', 'on', 'at', 'es', 'ed',
        'or', 'te', 'of', 'it', 'is', 'al', 'ar', 'st', 'to', 'nt',
        'ng', 're', 'ha', 'nd', 'ou', 'ea', 'le', 'se', 'as', 'io',
        'ne', 'me', 'co', 'de', 'ti', 'ri', 've', 'el', 'li', 'ra',
        'ce', 'la', 'ro', 'ta', 'ma', 'ic', 'no', 'ur', 'ch', 'ec',
    }

    # Common Turkish bigrams (top 30)
    TURKISH_BIGRAMS = {
        'la', 'ar', 'an', 'in', 'er', 'le', 'da', 'de', 'en', 'ir',
        'ak', 'al', 'bi', 'ka', 'ma', 'ya', 'ba', 'ol', 'il', 'ta',
        'li', 'si', 'ni', 'ri', 'nd', 'di', 'ki', 'me', 'ne', 'or',
    }

    def __init__(self):
        self.all_bigrams = self.ENGLISH_BIGRAMS | self.TURKISH_BIGRAMS

    def score(self, text: str) -> float:
        """
        Score text coherence (0.0 = garbled, 1.0 = natural).

        Args:
            text: Text to score

        Returns:
            Coherence score between 0.0 and 1.0
        """
        if not text or len(text) < 10:
            return 0.5  # Neutral for very short text

        # Clean text - lowercase, remove non-alpha
        clean = re.sub(r'[^a-zA-ZğüşıöçĞÜŞİÖÇ]', '', text.lower())
        if len(clean) < 6:
            return 0.5

        # Extract bigrams
        bigrams = [clean[i:i+2] for i in range(len(clean) - 1)]
        if not bigrams:
            return 0.5

        # Count how many bigrams are common
        common_count = sum(1 for bg in bigrams if bg in self.all_bigrams)
        ratio = common_count / len(bigrams)

        # Additional signals
        # Signal 1: Ratio of vowels (natural text ~40% vowels)
        vowels = set('aeiouıöüAEIOUİÖÜ')
        vowel_ratio = sum(1 for c in clean if c in vowels) / max(len(clean), 1)
        vowel_score = 1.0 - abs(vowel_ratio - 0.40) * 3  # Penalize far from 40%
        vowel_score = max(0.0, min(1.0, vowel_score))

        # Signal 2: Word length distribution (garbled text has unusual word lengths)
        words = text.split()
        if words:
            avg_word_len = sum(len(w) for w in words) / len(words)
            # Normal avg word length: 4-7 characters
            length_score = 1.0 - abs(avg_word_len - 5.5) / 5.0
            length_score = max(0.0, min(1.0, length_score))
        else:
            length_score = 0.5

        # Combined score
        score = ratio * 0.5 + vowel_score * 0.25 + length_score * 0.25
        return max(0.0, min(1.0, score))

    def is_incoherent(self, text: str, threshold: float = 0.25) -> bool:
        """Check if text is incoherent (below threshold)."""
        return self.score(text) < threshold


# =============================================================================
# 4. ENHANCED CITATION / BIBLIOGRAPHY DETECTION
# =============================================================================

class CitationDetector:
    """
    Detect inline citations and bibliography-formatted text.

    Goes beyond section-level bibliography detection to catch:
    - Inline references: (Author, 2020), [1], et al.
    - Reference list entries: "Smith, J. (2020). Title. Journal, 1(2), 3-4."
    - DOI patterns, URLs
    - Journal names commonly confused with policies
    """

    # Journal names that get confused with policies/institutions
    JOURNAL_NAMES = {
        'marine policy', 'ocean policy', 'energy policy', 'food policy',
        'land use policy', 'environmental policy', 'forest policy',
        'ocean & coastal management', 'ocean and coastal management',
        'marine pollution bulletin', 'marine ecology progress series',
        'journal of environmental management', 'ecological indicators',
        'environmental science & policy', 'environmental modelling',
        'renewable and sustainable energy reviews', 'renewable energy',
        'coastal engineering', 'ocean engineering', 'estuarine coastal',
        'biological conservation', 'conservation biology', 'nature',
        'science', 'plos one', 'frontiers in marine science',
    }

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile citation detection patterns."""
        # Inline citation patterns
        self.inline_patterns = [
            # (Author, 2020) or (Author et al., 2020)
            re.compile(r'\([A-Z][a-z]+(?:\s+(?:et\s+al\.?|and|&)\s+[A-Z][a-z]+)?,\s*\d{4}[a-z]?\)', re.UNICODE),
            # [1], [2,3], [1-5]
            re.compile(r'\[\d+(?:[,;\s-]+\d+)*\]'),
            # Author et al. (2020)
            re.compile(r'[A-Z][a-z]+\s+et\s+al\.?\s*\(\d{4}\)'),
            # Author and Author (2020)
            re.compile(r'[A-Z][a-z]+\s+(?:and|&)\s+[A-Z][a-z]+\s*\(\d{4}\)'),
        ]

        # Reference entry patterns (bibliography format)
        self.ref_entry_patterns = [
            # "Author, A. B. (2020). Title..."
            re.compile(r'^[A-Z][a-z]+,\s*[A-Z]\.?\s*(?:[A-Z]\.?\s*)?\(\d{4}\)\.', re.MULTILINE),
            # DOI patterns
            re.compile(r'(?:doi|DOI)[:\s]*10\.\d{4,}'),
            re.compile(r'https?://(?:dx\.)?doi\.org/10\.\d{4,}'),
            # "Vol. X, No. Y, pp. Z-W"
            re.compile(r'(?:Vol\.?|Volume)\s*\d+.*?(?:pp?\.?\s*\d+|No\.?\s*\d+)', re.IGNORECASE),
            # ISSN/ISBN
            re.compile(r'(?:ISSN|ISBN)[\s:-]*[\dX-]+'),
        ]

        # Journal name pattern
        journal_pattern = '|'.join(re.escape(j) for j in self.JOURNAL_NAMES)
        self.journal_pattern = re.compile(rf'\b({journal_pattern})\b', re.IGNORECASE)

    def is_citation_text(self, text: str) -> Tuple[bool, str]:
        """
        Check if text appears to be from a citation or bibliography entry.

        Args:
            text: Text to check

        Returns:
            Tuple of (is_citation, reason)
        """
        if not text:
            return False, ""

        # Check inline citation patterns
        for pattern in self.inline_patterns:
            matches = pattern.findall(text)
            if len(matches) >= 2:  # Multiple citations = likely bibliography content
                return True, "multiple_inline_citations"

        # Check reference entry format
        for pattern in self.ref_entry_patterns:
            if pattern.search(text):
                return True, "reference_entry_format"

        # Check if text is primarily a journal name
        text_lower = text.lower().strip()
        if self.journal_pattern.search(text_lower):
            # Check if the journal name IS the extraction (not just mentioned)
            match = self.journal_pattern.search(text_lower)
            if match and len(match.group()) > len(text_lower) * 0.5:
                return True, f"journal_name({match.group()})"

        return False, ""

    def count_citations_in_context(self, context: str) -> int:
        """Count number of inline citations in context text."""
        count = 0
        for pattern in self.inline_patterns:
            count += len(pattern.findall(context))
        return count

    def is_journal_name(self, text: str) -> bool:
        """Check if text is a journal name."""
        text_lower = text.lower().strip()
        # Remove common prefixes
        for prefix in ['the ', 'a ']:
            if text_lower.startswith(prefix):
                text_lower = text_lower[len(prefix):]
        return text_lower in self.JOURNAL_NAMES


# =============================================================================
# 5. SPECIES-SPECIFIC VALIDATION
# =============================================================================

class SpeciesValidator:
    """
    Validate species extractions using linguistic patterns.

    Rejects:
    - Generic group names (whale, coral, fish) without species qualifier
    - Place names containing species-like words (Coral Sea, Whale Bay)
    - Journal titles containing species words
    """

    # Generic group names that are NOT species
    GENERIC_GROUPS = {
        'whale', 'dolphin', 'shark', 'turtle', 'seal', 'seabird', 'bird',
        'fish', 'coral', 'kelp', 'algae', 'plankton', 'phytoplankton',
        'zooplankton', 'cetacean', 'mammal', 'invertebrate', 'vertebrate',
        'crustacean', 'mollusk', 'mollusc', 'seaweed', 'sponge',
        'tuna', 'cod', 'herring', 'sardine', 'anchovy', 'mackerel',
        'porpoise', 'ray', 'skate', 'eel', 'squid', 'octopus',
        'shrimp', 'prawn', 'lobster', 'crab', 'mussel', 'oyster',
        'clam', 'scallop', 'abalone',
    }

    # Place names that contain species-like words
    PLACE_NAMES = {
        'coral sea', 'whale bay', 'turtle island', 'dolphin coast',
        'seal beach', 'crab island', 'shark bay', 'fish creek',
    }

    # Binomial name pattern (genus + species)
    BINOMIAL_PATTERN = re.compile(
        r'^[A-Z][a-z]{2,}\s+[a-z]{2,}$'  # Genus species
    )

    def validate(self, text: str, context: str = "") -> Tuple[bool, float, str]:
        """
        Validate a species extraction.

        Args:
            text: Extracted species text
            context: Surrounding context text

        Returns:
            Tuple of (is_valid, confidence_adjustment, reason)
        """
        text_clean = text.strip()
        text_lower = text_clean.lower()

        # Accept binomial scientific names (highest confidence)
        if self.BINOMIAL_PATTERN.match(text_clean):
            return True, 1.5, "binomial_scientific_name"

        # Reject place names
        if text_lower in self.PLACE_NAMES:
            return False, 0.0, f"place_name({text_lower})"

        # Check for generic group names
        words = text_lower.split()
        if len(words) == 1 and text_lower in self.GENERIC_GROUPS:
            # Single generic word - needs qualifier in context
            context_lower = context.lower() if context else ""
            has_qualifier = any(q in context_lower for q in [
                'species', 'population', 'habitat', 'abundance',
                'distribution', 'conservation', 'threatened', 'endangered',
                'protected', 'monitoring', 'survey', 'breeding',
            ])
            if has_qualifier:
                return True, 0.7, "generic_with_qualifier"
            else:
                return False, 0.0, f"generic_group_no_qualifier({text_lower})"

        # Multi-word common names - generally OK
        if len(words) >= 2:
            # Check if it's a meaningful species name (e.g., "bottlenose dolphin")
            return True, 1.0, "multi_word_common_name"

        return True, 0.8, "species_default"


# =============================================================================
# 6. COMBINED NLP FILTER
# =============================================================================

class NLPFilter:
    """
    Combined NLP filter that applies all validation techniques.

    This is the main interface used by the extraction pipeline.
    """

    def __init__(self):
        self.ner_validator = NERValidator()
        self.pos_garble = POSGarbleDetector()
        self.coherence = CoherenceScorer()
        self.citation = CitationDetector()
        self.species_validator = SpeciesValidator()
        logger.info("NLP filters initialized (NLTK NER, POS, coherence, citation, species)")

    def validate_extraction(self, text: str, category: str,
                           context: str = "", sentence: str = "") -> Dict:
        """
        Validate an extraction using all NLP techniques.

        Args:
            text: The extracted text
            category: Extraction category
            context: Broader context text
            sentence: The sentence containing the extraction

        Returns:
            Dict with:
                - is_valid: bool
                - confidence_multiplier: float (0.0-1.5)
                - reasons: list of reason strings
                - nlp_score: float (0.0-1.0, overall quality)
        """
        reasons = []
        multipliers = []
        is_valid = True

        # 1. Citation check (fast, applies to all)
        is_cite, cite_reason = self.citation.is_citation_text(text)
        if is_cite:
            is_valid = False
            reasons.append(f"citation:{cite_reason}")
            return {
                'is_valid': False,
                'confidence_multiplier': 0.0,
                'reasons': reasons,
                'nlp_score': 0.0,
            }

        # Also check if context is citation-heavy
        if context:
            cite_count = self.citation.count_citations_in_context(context)
            if cite_count >= 3:
                reasons.append(f"high_citation_context({cite_count})")
                multipliers.append(0.5)

        # 2. Coherence check (lightweight, applies to all)
        coherence_score = self.coherence.score(text)
        if coherence_score < 0.20:
            is_valid = False
            reasons.append(f"incoherent({coherence_score:.2f})")
            return {
                'is_valid': False,
                'confidence_multiplier': 0.0,
                'reasons': reasons,
                'nlp_score': coherence_score,
            }
        elif coherence_score < 0.35:
            reasons.append(f"low_coherence({coherence_score:.2f})")
            multipliers.append(0.6)

        # 3. POS-based garble detection (for longer text)
        if len(text) > 30:
            is_garbled, garble_reason = self.pos_garble.is_garbled(text)
            if is_garbled:
                is_valid = False
                reasons.append(f"pos_garble:{garble_reason}")
                return {
                    'is_valid': False,
                    'confidence_multiplier': 0.0,
                    'reasons': reasons,
                    'nlp_score': 0.1,
                }

        # 4. Category-specific validation
        if category == 'species':
            sp_valid, sp_mult, sp_reason = self.species_validator.validate(text, context)
            if not sp_valid:
                is_valid = False
                reasons.append(f"species:{sp_reason}")
                return {
                    'is_valid': False,
                    'confidence_multiplier': 0.0,
                    'reasons': reasons,
                    'nlp_score': 0.1,
                }
            multipliers.append(sp_mult)
            if sp_reason != "species_default":
                reasons.append(f"species:{sp_reason}")

        elif category in ('stakeholder', 'institution', 'policy'):
            # NER validation
            ner_valid, ner_mult, ner_reason = self.ner_validator.validate(text, category)
            multipliers.append(ner_mult)
            if ner_reason not in ("ner_not_applicable", "too_short_for_ner", "ner_error"):
                reasons.append(f"ner:{ner_reason}")

            # Journal name check for policy
            if category == 'policy' and self.citation.is_journal_name(text):
                is_valid = False
                reasons.append("policy_is_journal_name")
                return {
                    'is_valid': False,
                    'confidence_multiplier': 0.0,
                    'reasons': reasons,
                    'nlp_score': 0.1,
                }

        # Compute final multiplier
        if multipliers:
            final_mult = 1.0
            for m in multipliers:
                final_mult *= m
            # Clamp
            final_mult = max(0.1, min(1.5, final_mult))
        else:
            final_mult = 1.0

        # Overall NLP score
        nlp_score = coherence_score * final_mult

        return {
            'is_valid': is_valid,
            'confidence_multiplier': final_mult,
            'reasons': reasons,
            'nlp_score': min(1.0, nlp_score),
        }


# =============================================================================
# 7. TF-IDF CATEGORY CLASSIFIER (trainable from validation data)
# =============================================================================

class CategoryClassifier:
    """
    TF-IDF + Logistic Regression classifier trained on annotated validation data.

    Predicts whether an extraction is correct for its assigned category.
    Uses exact_text + context features.
    """

    def __init__(self):
        self.model = None
        self.vectorizer = None
        self._trained = False

    def train_from_validation_sheets(self, sheets_dir: str) -> Dict:
        """
        Train classifier from annotated validation CSVs.

        Args:
            sheets_dir: Directory with validate_*.csv files

        Returns:
            Training metrics dict
        """
        import csv
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import cross_val_score

        sheets_path = Path(sheets_dir)
        texts = []
        labels = []

        for csv_file in sorted(sheets_path.glob("validate_*.csv")):
            category = csv_file.stem.replace("validate_", "")
            try:
                with open(csv_file, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        is_correct = row.get('is_correct', '').strip().lower()
                        if is_correct not in ('y', 'n'):
                            continue

                        exact = row.get('exact_text', '')
                        context = row.get('context', '')
                        # Feature: category + text + context
                        feature_text = f"[{category}] {exact} ||| {context}"
                        texts.append(feature_text)
                        labels.append(1 if is_correct == 'y' else 0)
            except Exception as e:
                logger.warning(f"Error reading {csv_file}: {e}")

        if len(texts) < 50:
            logger.warning(f"Too few training samples ({len(texts)}), skipping classifier")
            return {'status': 'insufficient_data', 'n_samples': len(texts)}

        # Train
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            min_df=2,
            sublinear_tf=True,
        )
        X = self.vectorizer.fit_transform(texts)
        y = labels

        self.model = LogisticRegression(
            C=1.0,
            class_weight='balanced',
            max_iter=1000,
            random_state=42,
        )
        self.model.fit(X, y)

        # Cross-validation score
        cv_scores = cross_val_score(self.model, X, y, cv=5, scoring='precision')

        self._trained = True
        n_pos = sum(labels)
        n_neg = len(labels) - n_pos

        metrics = {
            'status': 'trained',
            'n_samples': len(texts),
            'n_positive': n_pos,
            'n_negative': n_neg,
            'cv_precision_mean': float(cv_scores.mean()),
            'cv_precision_std': float(cv_scores.std()),
        }

        logger.info(f"Category classifier trained: {len(texts)} samples, "
                    f"CV precision: {cv_scores.mean():.3f} +/- {cv_scores.std():.3f}")

        return metrics

    def predict(self, text: str, category: str, context: str = "") -> Tuple[float, bool]:
        """
        Predict if extraction is correct.

        Args:
            text: Extracted text
            category: Category name
            context: Context text

        Returns:
            Tuple of (probability_correct, is_likely_correct)
        """
        if not self._trained:
            return 0.5, True  # Neutral if not trained

        feature_text = f"[{category}] {text} ||| {context}"
        X = self.vectorizer.transform([feature_text])
        prob = self.model.predict_proba(X)[0]

        # prob[1] = probability of being correct
        p_correct = float(prob[1]) if len(prob) > 1 else 0.5
        is_correct = p_correct > 0.5

        return p_correct, is_correct
