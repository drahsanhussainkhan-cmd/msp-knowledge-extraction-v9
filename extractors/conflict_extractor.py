"""
Conflict Extractor v2 - Enhanced
Extracts use conflicts, incompatibilities, and resolution strategies from MSP documents.
Supports conflict taxonomy (spatial/temporal/resource/governance), activity normalization,
and resolution extraction using natural language patterns.
"""
import re
import logging
from typing import Dict, List, Optional

try:
    from ..core.enums import DocumentType
    from ..data_structures import ConflictExtraction
    from .base_extractor import BaseExtractor
except ImportError:
    from core.enums import DocumentType
    from data_structures import ConflictExtraction
    from extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class ConflictExtractor(BaseExtractor):
    """Extract use conflicts from scientific papers and legal documents"""

    # Non-marine terms that indicate algorithmic/technical conflicts (not MSP)
    NON_MARINE_TERMS = frozenset({
        'dataset', 'algorithm', 'model', 'parameter', 'convergence',
        'path', 'node', 'robot', 'vehicle', 'sensor', 'network',
        'method', 'function', 'variable', 'equation', 'objective',
        'optimization', 'pixel', 'layer', 'training', 'epoch',
        'gradient', 'loss', 'batch', 'neural', 'classifier',
        'trajectory', 'waypoint', 'obstacle',
        'computation', 'complexity', 'efficiency', 'accuracy',
        'matlab', 'comsol', 'python', 'software',
        'cost', 'budget', 'revenue',
        # Physical/natural processes (not human use conflicts)
        'waves', 'wave', 'currents', 'current', 'tides', 'tide',
        'storm', 'sediment', 'erosion', 'polymer', 'grids', 'grid',
        'stressors', 'organisms', 'structures', 'introduction',
        # Environment/nature terms (not human use activities)
        'environment', 'environmental', 'ecological',
        'quality', 'climate', 'sea level', 'rising',
        'communities', 'target species',
    })

    # Garble-start words indicating fragment, not real activity
    GARBLE_STARTS = frozenset({
        'a ', 'an ', 'the ', 'is ', 'are ', 'was ', 'were ',
        'has ', 'had ', 'have ', 'do ', 'does ', 'did ',
        've ', 's ', 't ', 'to ', 'of ', 'in ', 'on ',
        'it ', 'we ', 'he ', 'she ', 'or ', 'if ',
        'can ', 'could ', 'would ', 'should ', 'may ', 'might ',
        'been ', 'being ', 'also ', 'not ', 'but ', 'so ',
    })

    # Words that signal end of an activity phrase (sentence continuation)
    ACTIVITY_STOP_WORDS = frozenset({
        'was', 'were', 'is', 'are', 'has', 'have', 'had', 'will',
        'because', 'although', 'according', 'where', 'which', 'that',
        'this', 'these', 'those', 'based', 'such', 'however',
        'while', 'when', 'since', 'through', 'from', 'into',
        'about', 'after', 'before', 'during', 'within', 'without',
        'green', 'red', 'blue',  # color words from maps
        'of', 'at', 'as', 'for', 'across', 'collectively',
        'and', 'or', 'various', 'several', 'different', 'other',
        # Common past participles / verbs (not activities)
        'presented', 'discussed', 'studied', 'observed', 'reported',
        'described', 'identified', 'proposed', 'found', 'shown',
        'suggested', 'indicated', 'demonstrated', 'considered',
    })

    # Too-generic single-word "activities" that produce false positives
    GENERIC_TERMS = frozenset({
        'uses', 'users', 'use', 'areas', 'area', 'activities',
        'sectors', 'sector', 'study', 'studies', 'data',
        'results', 'methods', 'zones', 'zone', 'limits',
        'and', 'or', 'the', 'of', 'to', 'in', 'on', 'by',
        'for', 'at', 'as', 'with', 'from', 'time',
    })

    def _compile_patterns(self):
        """Compile conflict patterns - expanded for higher recall"""

        # ── Turkish patterns ──
        self.turkish_patterns = [
            # Original: X ile Y arasında çatışma/uyumsuzluk/çelişki/çakışma
            re.compile(
                r'(?P<activity1>[\w\s]+?)\s+(?:ile|ve)\s+(?P<activity2>[\w\s]+?)\s+'
                r'(?:aras[ıi]nda\s+)?(?P<type>çat[ıi][şs]ma|uyumsuzluk|çeli[şs]ki|ç[aâ]k[ıi][şs]ma)',
                re.IGNORECASE | re.UNICODE
            ),
            # Competition: X ile Y arasında rekabet/gerilim/anlaşmazlık
            re.compile(
                r'(?P<activity1>[\w\s]+?)\s+(?:ile|ve)\s+(?P<activity2>[\w\s]+?)\s+'
                r'(?:aras[ıi]nda\s+)?(?P<type>rekabet|gerilim|anla[şs]mazl[ıi]k)',
                re.IGNORECASE | re.UNICODE
            ),
            # Threat: X ... Y'yi tehdit ediyor
            re.compile(
                r'(?P<activity1>[\w\s]{3,40}?)\s+(?P<activity2>[\w\s]{3,40}?)\s*'
                r'(?:için|açısından)?\s*(?P<type>tehdit)\s+(?:ediyor|etmektedir|eder|etmekte)',
                re.IGNORECASE | re.UNICODE
            ),
            # Negative impact: X ... Y üzerinde olumsuz etki
            re.compile(
                r'(?P<activity1>[\w\s]{3,40}?)\s+(?P<activity2>[\w\s]{3,40}?)\s+'
                r'üzerinde\s+(?P<type>olumsuz\s+etki)',
                re.IGNORECASE | re.UNICODE
            ),
        ]

        # ── English patterns ──
        self.english_patterns = [
            # --- Original patterns (refined with [^,]+? for cleaner boundaries) ---

            # "conflict/incompatibility between X and Y"
            re.compile(
                r'(?P<type>conflicts?|incompatibility)\s+between\s+'
                r'(?P<activity1>[^,;.]+?)\s+and\s+(?P<activity2>[^,.;\[\]()\n\r<>]{3,40})',
                re.IGNORECASE
            ),
            # "X conflicts/incompatible with Y"
            re.compile(
                r'(?P<activity1>[^,;.]+?)\s+(?:conflicts?|incompatible)\s+with\s+'
                r'(?P<activity2>[^,.;\[\]()\n\r<>]{3,40})',
                re.IGNORECASE
            ),

            # --- New patterns for higher recall ---

            # "competition/rivalry between X and Y"
            re.compile(
                r'(?P<type>competition|rivalry)\s+between\s+'
                r'(?P<activity1>[^,;.]+?)\s+and\s+(?P<activity2>[^,.;\[\]()\n\r<>]{3,40})',
                re.IGNORECASE
            ),
            # "tensions/disputes between/among X and Y"
            re.compile(
                r'(?P<type>tensions?|disputes?)\s+(?:between|among)\s+'
                r'(?P<activity1>[^,;.]+?)\s+and\s+(?P<activity2>[^,.;\[\]()\n\r<>]{3,40})',
                re.IGNORECASE
            ),
            # "trade-off(s) between X and Y"
            re.compile(
                r'(?P<type>trade-?offs?|tradeoffs?)\s+between\s+'
                r'(?P<activity1>[^,;.]+?)\s+and\s+(?P<activity2>[^,.;\[\]()\n\r<>]{3,40})',
                re.IGNORECASE
            ),
            # "displacement of X by Y"
            re.compile(
                r'(?P<type>displacement)\s+of\s+'
                r'(?P<activity1>[^,;.]+?)\s+by\s+(?P<activity2>[^,.;\[\]()\n\r<>]{3,40})',
                re.IGNORECASE
            ),
            # "X was/were displaced by Y"
            re.compile(
                r'(?P<activity1>[^,;.]+?)\s+(?:was|were|been)\s+(?P<type>displaced)\s+by\s+'
                r'(?P<activity2>[^,.;\[\]()\n\r<>]{3,40})',
                re.IGNORECASE
            ),
            # "overlap between/of X and Y"
            re.compile(
                r'(?P<type>overlap(?:ping)?)\s+(?:between|of)\s+'
                r'(?P<activity1>[^,;.]+?)\s+and\s+(?P<activity2>[^,.;\[\]()\n\r<>]{3,40})',
                re.IGNORECASE
            ),
            # "competing uses/activities/interests such as X and Y" or "competing X and Y"
            re.compile(
                r'(?P<type>competing)\s+(?:uses?|activities|interests|demands?)'
                r'(?:\s+(?:such\s+as|including|like))?\s+'
                r'(?P<activity1>[^,;.]+?)\s+and\s+(?P<activity2>[^,.;\[\]()\n\r<>]{3,40})',
                re.IGNORECASE
            ),
            # "X and Y are incompatible/mutually exclusive"
            re.compile(
                r'(?P<activity1>[^,;.\[\]()\n\r<>]{3,40}?)\s+and\s+(?P<activity2>[^,;.\[\]()\n\r<>]{3,40}?)\s+'
                r'(?:are|were|is)\s+(?P<type>incompatible|mutually\s+exclusive)',
                re.IGNORECASE
            ),
            # "X threatens Y" / "X poses a threat to Y"
            re.compile(
                r'(?P<activity1>[^,;.\[\]()\n\r<>]{3,40}?)\s+'
                r'(?P<type>threatens?|poses?\s+(?:a\s+)?threat\s+to)\s+'
                r'(?P<activity2>[^,.;\[\]()\n\r<>]{3,40})',
                re.IGNORECASE
            ),
            # "X clashes with Y"
            re.compile(
                r'(?P<activity1>[^,;.]+?)\s+(?P<type>clash(?:es)?)\s+with\s+'
                r'(?P<activity2>[^,.;\[\]()\n\r<>]{3,40})',
                re.IGNORECASE
            ),
            # "interaction/interference between X and Y"
            re.compile(
                r'(?:negative\s+)?(?P<type>interact(?:ion|ions)|interference)\s+between\s+'
                r'(?P<activity1>[^,;.]+?)\s+and\s+(?P<activity2>[^,.;\[\]()\n\r<>]{3,40})',
                re.IGNORECASE
            ),
        ]

    def extract(self, text: str, page_texts: Dict[int, str],
                doc_type: DocumentType) -> List[ConflictExtraction]:
        """Extract conflicts from text"""
        results: List[ConflictExtraction] = []
        language = self._get_language(doc_type)

        patterns = self.turkish_patterns if language == "turkish" else self.english_patterns

        for pattern in patterns:
            for match in pattern.finditer(text):
                result = self._process_match(match, text, text, page_texts, language, doc_type)
                if result:
                    results.append(result)

        return self._deduplicate(results)

    def _process_match(self, match: re.Match, converted_text: str, original_text: str,
                       page_texts: Dict[int, str], language: str,
                       doc_type: DocumentType) -> Optional[ConflictExtraction]:
        """Process a conflict match"""
        try:
            # Skip bibliography and garbled text
            if self._should_skip_match(converted_text, match.start(), match.group(0), category="conflict"):
                return None

            groups = match.groupdict()
            sentence, context = self._get_sentence_context(converted_text, match.start(), match.end())

            marine_score = self.fp_filter.get_marine_relevance_score(sentence, language)
            if marine_score < 0.15:
                return None

            raw_activity_1 = (groups.get('activity1') or '').strip()[:50]
            raw_activity_2 = (groups.get('activity2') or '').strip()[:50]

            # Reject activities that are too long (boundary detection failure)
            if len(raw_activity_1) > 40 or len(raw_activity_2) > 40:
                return None

            # Validate both activities
            if not self._is_valid_activity(raw_activity_1) or not self._is_valid_activity(raw_activity_2):
                return None

            # Reject non-marine conflicts
            act_combined = (raw_activity_1 + ' ' + raw_activity_2).lower()
            if any(t in act_combined for t in self.NON_MARINE_TERMS):
                return None

            # Reject garbled unicode (replacement character)
            if '\ufffd' in raw_activity_1 or '\ufffd' in raw_activity_2 or '\ufffd' in sentence:
                return None

            # Clean activities using keyword dictionary
            activity_1 = self._clean_activity(raw_activity_1, sentence, language)
            activity_2 = self._clean_activity(raw_activity_2, sentence, language)

            # Reject same-activity conflicts (e.g., "shrimp vs shrimp")
            if activity_1.lower().strip() == activity_2.lower().strip():
                return None

            # Require at least one activity to have marine/MSP content
            if not (self._has_marine_keyword(activity_1, language) or
                    self._has_marine_keyword(activity_2, language)):
                return None

            # Get broader context for resolution search (±500 chars)
            broad_start = max(0, match.start() - 500)
            broad_end = min(len(converted_text), match.end() + 500)
            broad_context = converted_text[broad_start:broad_end]

            # Classify conflict type
            conflict_type = self._classify_conflict_type(context, activity_1, activity_2, language)

            severity = self._extract_severity(context, language)
            resolution = self._extract_resolution(broad_context, language)

            page_num = self._find_page_number(match.start(), page_texts)

            confidence = 0.7
            if marine_score > 0.3:
                confidence += 0.1
            if severity:
                confidence += 0.05
            if resolution:
                confidence += 0.05
            if conflict_type != 'spatial':  # classified into specific type
                confidence += 0.05

            return ConflictExtraction(
                conflict_type=conflict_type,
                activity_1=activity_1 if activity_1 else None,
                activity_2=activity_2 if activity_2 else None,
                severity=severity,
                resolution=resolution,
                context=context[:300],
                exact_text=match.group(0),
                page_number=page_num,
                confidence=min(confidence, 1.0),
                marine_relevance=marine_score
            )

        except Exception as e:
            logger.warning(f"Error processing conflict match: {e}")
            return None

    def _is_valid_activity(self, act: str) -> bool:
        """Validate that an activity string is not garbled or too short."""
        if not act or len(act) < 3:
            return False
        if '\n' in act or '\r' in act:
            return False
        if len(act) > 20 and ' ' not in act:
            return False
        act_lower = act.lower().strip()
        if any(act_lower.startswith(g) for g in self.GARBLE_STARTS):
            return False
        # Reject if contains citation brackets or parentheses
        if re.search(r'[\[\]()]', act):
            return False
        # Reject if contains digits (stats like "<2%", "825 sites")
        if re.search(r'\d', act):
            return False
        # Reject if contains hyphenated line breaks (PDF artifacts like "envi- ronmental")
        if re.search(r'\w-\s+\w', act):
            return False
        # Reject if ends with hyphen (PDF line-break artifact like "protec-")
        if act.rstrip().endswith('-'):
            return False
        words = act_lower.split()
        if not any(len(w) >= 3 and w.isalpha() for w in words):
            return False
        # Reject if any word is a stop word (sentence continuation)
        if any(w in self.ACTIVITY_STOP_WORDS for w in words):
            return False
        # Reject too many words (real activities are 1-4 words)
        if len(words) > 4:
            return False
        # Reject single generic terms
        if len(words) == 1 and words[0] in self.GENERIC_TERMS:
            return False
        return True

    def _has_marine_keyword(self, text: str, language: str) -> bool:
        """Check if text contains at least one known marine/MSP keyword."""
        text_lower = text.lower()
        # Check against ACTIVITIES dictionary
        for activity_key, data in self.keywords.ACTIVITIES.items():
            kw_list = data.get(language, data.get('english', []))
            for kw in kw_list:
                if kw.lower() in text_lower:
                    return True
        # Common MSP terms not necessarily in ACTIVITIES
        marine_terms = {
            'marine', 'maritime', 'coastal', 'ocean', 'sea', 'port',
            'harbor', 'harbour', 'beach', 'shore', 'fishery', 'fisheries',
            'fishing', 'aquaculture', 'shipping', 'navigation', 'offshore',
            'wind farm', 'wind energy', 'oil', 'gas', 'pipeline', 'cable',
            'dredging', 'mining', 'conservation', 'mpa', 'mpas', 'isra',
            'isras', 'sanctuary', 'biodiversity', 'ecosystem', 'habitat',
            'species', 'whale', 'dolphin', 'turtle', 'coral', 'seabird',
            'tourism', 'recreation', 'diving', 'surfing', 'cetacean',
            'military', 'navy', 'defense', 'defence', 'trawling',
            'deniz', 'kıyı', 'balık', 'liman', 'iskele',
        }
        return any(t in text_lower for t in marine_terms)

    def _clean_activity(self, raw_text: str, sentence: str, language: str) -> str:
        """Map raw regex capture to a known MSP activity keyword, or clean it up."""
        raw_lower = raw_text.lower().strip()

        # First: check if any known activity keyword appears in the raw capture
        best_kw = None
        best_len = 0
        for activity_key, data in self.keywords.ACTIVITIES.items():
            kw_list = data.get(language, data.get('english', []))
            for kw in kw_list:
                if kw.lower() in raw_lower and len(kw) > best_len:
                    best_kw = kw
                    best_len = len(kw)
        if best_kw:
            return best_kw

        # Second: check the broader sentence for activity keywords near the raw text
        sent_lower = sentence.lower()
        raw_pos = sent_lower.find(raw_lower)
        if raw_pos >= 0:
            window = sent_lower[max(0, raw_pos - 40):raw_pos + len(raw_lower) + 40]
            best_kw = None
            best_len = 0
            for activity_key, data in self.keywords.ACTIVITIES.items():
                kw_list = data.get(language, data.get('english', []))
                for kw in kw_list:
                    if kw.lower() in window and len(kw) > best_len:
                        best_kw = kw
                        best_len = len(kw)
            if best_kw:
                return best_kw

        # Fallback: return cleaned raw text
        # Strip leading articles/prepositions
        cleaned = re.sub(
            r'^(?:the|a|an|of|for|in|on|by|to|and|with|their|our|its|these|those|some|this|that)\s+',
            '', raw_lower, flags=re.IGNORECASE
        )
        # Truncate at first stop word
        words = cleaned.split()
        truncated = []
        for w in words:
            if w in self.ACTIVITY_STOP_WORDS:
                break
            truncated.append(w)
        if not truncated:
            truncated = words[:1]
        # Max 3 words for fallback
        return ' '.join(truncated[:3])

    def _classify_conflict_type(self, context: str, activity_1: str, activity_2: str, language: str) -> str:
        """Classify conflict type based on context keywords."""
        text = f"{context} {activity_1} {activity_2}".lower()

        temporal_kw = [
            'season', 'seasonal', 'temporal', 'time', 'month', 'winter', 'summer',
            'spring', 'autumn', 'spawning period', 'breeding season', 'closure period',
            'time-sharing', 'scheduling',
            'mevsim', 'mevsimsel', 'dönem', 'yumurtlama', 'üreme',
        ]
        resource_kw = [
            'stock', 'resource', 'carrying capacity', 'biomass', 'depletion',
            'overexploit', 'overfishing', 'water quality', 'nutrient', 'pollution',
            'eutrophication', 'degradation', 'fish stock',
            'stok', 'kaynak', 'taşıma kapasitesi', 'kirlilik', 'aşırı avlanma',
        ]
        governance_kw = [
            'jurisdiction', 'authority', 'institutional', 'regulatory', 'governance',
            'mandate', 'competence', 'coordination', 'transboundary', 'cross-border',
            'legal framework', 'policy gap',
            'yetki', 'kurumsal', 'düzenleyici', 'koordinasyon', 'sınır ötesi',
        ]
        spatial_kw = [
            'space', 'spatial', 'area', 'zone', 'overlap', 'displace', 'displacement',
            'buffer', 'location', 'site', 'territory', 'co-location', 'colocation',
            'siting', 'adjacent',
            'alan', 'bölge', 'yer', 'konumlandırma',
        ]

        scores = {
            'temporal': sum(1 for k in temporal_kw if k in text),
            'resource': sum(1 for k in resource_kw if k in text),
            'governance': sum(1 for k in governance_kw if k in text),
            'spatial': sum(1 for k in spatial_kw if k in text),
        }
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else 'spatial'

    def _extract_severity(self, context: str, language: str) -> Optional[str]:
        """Extract conflict severity from context keywords."""
        context_lower = context.lower()

        if language == 'turkish':
            if any(x in context_lower for x in ['yüksek', 'ciddi', 'şiddetli', 'önemli', 'büyük']):
                return 'high'
            elif any(x in context_lower for x in ['orta', 'normal']):
                return 'medium'
            elif any(x in context_lower for x in ['düşük', 'az', 'küçük', 'sınırlı']):
                return 'low'
        else:
            if any(x in context_lower for x in ['high', 'severe', 'major', 'significant',
                                                  'serious', 'critical', 'intense']):
                return 'high'
            elif any(x in context_lower for x in ['medium', 'moderate']):
                return 'medium'
            elif any(x in context_lower for x in ['low', 'minor', 'small', 'limited', 'minimal']):
                return 'low'

        return None

    # Known resolution strategy terms for pattern matching
    RESOLUTION_STRATEGIES = [
        'spatial zoning', 'temporal zoning', 'zoning', 'buffer zone',
        'stakeholder consultation', 'stakeholder engagement', 'stakeholder dialogue',
        'stakeholder participation', 'co-location', 'colocation',
        'seasonal restriction', 'seasonal closure', 'time-sharing',
        'marine spatial planning', 'ecosystem-based management',
        'adaptive management', 'integrated management',
        'quota system', 'quota allocation', 'exclusion zone', 'no-take zone',
        'marine protected area', 'spatial planning', 'management plan',
        'negotiation', 'mediation', 'compensation', 'mitigation',
        'separation of uses', 'co-existence', 'coexistence',
        'priority setting', 'multi-use', 'multi-objective',
    ]

    def _extract_resolution(self, context: str, language: str) -> Optional[str]:
        """Extract conflict resolution strategies from broader context."""
        context_lower = context.lower()

        if language == 'turkish':
            patterns = [
                r'(?:çözüm\s+olarak|çözmek\s+için|gidermek\s+amacıyla)\s+([^.;\n]{10,80})',
                r'(zonlama|tampon\s+bölge|mevsimsel\s+k[ıi]s[ıi]tlama|payda[şs]\s+kat[ıi]l[ıi]m[ıi])',
            ]
            for pattern in patterns:
                match = re.search(pattern, context, re.IGNORECASE | re.UNICODE)
                if match:
                    result = match.group(1).strip()
                    if len(result) >= 5:
                        return result[:80]
        else:
            # Strategy 1: Look for known resolution terms in context
            for strategy in self.RESOLUTION_STRATEGIES:
                if strategy in context_lower:
                    return strategy

            # Strategy 2: "through/via/using [resolution phrase]" near conflict keywords
            pattern = (
                r'(?:through|via|using|by)\s+'
                r'((?:spatial|temporal)\s+zoning|buffer\s+zones?|'
                r'stakeholder\s+\w+|co-?location|seasonal\s+\w+|'
                r'marine\s+spatial\s+planning|'
                r'(?:adaptive|ecosystem[- ]based|integrated)\s+management|'
                r'quota\s+\w+|exclusion\s+zones?|no-?take\s+zones?|'
                r'negotiat\w+|mediat\w+|compensat\w+|mitigat\w+)'
            )
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:80]

            # Strategy 3: "resolved/addressed/managed through/by [phrase]"
            pattern = (
                r'(?:resolved?|addressed|managed|mitigated)\s+'
                r'(?:through|by|via|using)\s+([^.;\n]{8,60})'
            )
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                result = match.group(1).strip()
                result = re.sub(r'^(?:the|a|an)\s+', '', result, flags=re.IGNORECASE)
                # Only accept if it contains meaningful words (not just "between X and Y")
                if 'between' not in result.lower() and len(result) >= 8:
                    return result[:80]

        return None
