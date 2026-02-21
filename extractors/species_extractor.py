"""
Species Extractor - Extracts species mentions from legal and scientific texts
Fixed: removed overly broad scientific name pattern that caused massive false positives
"""
import re
import logging
from typing import Dict, List, Optional

try:
    from ..core.enums import DocumentType
    from ..data_structures import SpeciesExtraction
    from .base_extractor import BaseExtractor
except ImportError:
    from core.enums import DocumentType
    from data_structures import SpeciesExtraction
    from extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class SpeciesExtractor(BaseExtractor):
    """Extract species mentions from MSP documents"""

    # Words that look like "Genus species" but are not biological names
    SCIENTIFIC_NAME_BLACKLIST = {
        # Turkish sentence starters & legal terms (lowercase first word)
        'bu', 'devlet', 'kanun', 'madde', 'ancak', 'birinci', 'ikinci',
        'bunlar', 'hususi', 'vilayet', 'vali', 'tehlike', 'bakanlar',
        'belediye', 'imar', 'arazi', 'tapu', 'yetki', 'genel', 'özel',
        # English non-species words
        'marine', 'ocean', 'coastal', 'spatial', 'figure', 'table',
        'section', 'chapter', 'results', 'methods', 'however', 'although',
        'during', 'within', 'between', 'through', 'according', 'based',
        'using', 'following', 'including', 'regarding', 'concerning',
        'contents', 'available', 'journal', 'elsevier', 'springer',
        'copyright', 'published', 'received', 'accepted', 'revised',
        'abstract', 'introduction', 'discussion', 'conclusion', 'analysis',
        'research', 'science', 'policy', 'planning', 'management',
        'environmental', 'ecological', 'biological', 'statistical',
        'international', 'national', 'regional', 'european', 'united',
        'university', 'institute', 'department', 'ministry', 'government',
        # More false positive starters
        'supplementary', 'additional', 'corresponding', 'alternative',
        'significant', 'important', 'different', 'particular', 'potential',
        'essential', 'relevant', 'specific', 'general', 'various',
        'natural', 'physical', 'chemical', 'technical', 'practical',
        'current', 'present', 'previous', 'recent', 'initial',
        'total', 'local', 'global', 'primary', 'secondary',
        # CRediT author contributions (very common in papers)
        'formal', 'data', 'funding', 'project', 'writing',
        'conceptualization', 'methodology', 'software', 'validation',
        'investigation', 'resources', 'supervision', 'visualization',
        # Common non-species two-word patterns
        'communication', 'assessing', 'food', 'exclusion',
        'fisheries', 'the', 'for', 'from', 'with', 'this',
        'wang', 'ehler', 'douvere', 'smith', 'jones', 'chen',
        'zhang', 'liu', 'yang', 'huang', 'brown', 'johnson',
    }

    def _compile_patterns(self):
        """Compile species patterns for both languages"""
        # Turkish patterns - explicit species names only
        self.turkish_patterns = [
            # Fish species (Turkish common names) - comprehensive list
            re.compile(
                r'\b(?P<species>levrek|çipura|lüfer|hamsi|istavrit|kalkan|barbunya|mercan|orkinos|palamut|'
                r'uskumru|sardalya|mezgit|kefal|fangri|iskorpit|ahtapot|karides|midye|istridye|kalamar|'
                r'sazan|alabalık|somon|ton\s*balığı|kılıç\s*balığı|morina|pisi|dil\s*balığı|'
                r'tekir|trança|lagos|sinagrit|kolyoz|çinakop|sarıkanat|zargana|lüfer|'
                r'deniz\s*levreği|çupra|dülger|gelincik|karagöz)\b',
                re.IGNORECASE | re.UNICODE
            ),
            # Marine mammals & reptiles (Turkish)
            re.compile(
                r'\b(?P<species>yunus|fok|deniz\s+kaplumbağası|caretta\s+caretta|akdeniz\s+foku|'
                r'monachus\s+monachus|deniz\s+memelisi|balin[a])\b',
                re.IGNORECASE | re.UNICODE
            ),
            # Seagrass / algae (Turkish)
            re.compile(
                r'\b(?P<species>posidonia|posidonia\s+oceanica|deniz\s+çayırı|'
                r'deniz\s+yosunu|caulerpa|cymodocea)\b',
                re.IGNORECASE | re.UNICODE
            ),
        ]

        # English patterns
        self.english_patterns = [
            # Fish species (English common names) - prefer compound terms to avoid ambiguity
            re.compile(
                r'\b(?P<species>sea\s+bass|gilthead\s+bream|european\s+(?:bass|anchovy|hake|eel)|'
                r'atlantic\s+(?:cod|salmon|herring|mackerel|tuna|bluefin)|'
                r'bluefin\s+tuna|yellowfin\s+tuna|skipjack\s+tuna|'
                r'blue\s+(?:crab|mussel|shark|whale)|'
                r'red\s+(?:mullet|snapper|coral)|'
                r'spiny\s+lobster|horse\s+mackerel|'
                r'common\s+(?:sole|cuttlefish|dolphin)|'
                r'mediterranean\s+(?:mussel|monk\s+seal)|'
                r'tuna|anchovy|mackerel|sardine|mullet|grouper|seabream|'
                r'bluefish|octopus|squid|shrimp|mussel|oyster|'
                r'cod|salmon|herring|haddock|plaice|lobster|clam|scallop|'
                r'swordfish|hake|snapper|barracuda|wrasse|goby|whiting|'
                r'turbot|sturgeon|cuttlefish|jellyfish|starfish|sea\s+urchin|'
                r'sea\s+cucumber|seahorse|stingray|manta\s+ray)\b',
                re.IGNORECASE
            ),
            # Marine mammals & reptiles
            re.compile(
                r'\b(?P<species>dolphin|bottlenose\s+dolphin|common\s+dolphin|'
                r'monk\s+seal|harbor\s+seal|grey\s+seal|'
                r'sea\s+turtle|loggerhead\s+turtle|green\s+turtle|leatherback\s+turtle|'
                r'humpback\s+whale|sperm\s+whale|fin\s+whale|blue\s+whale|minke\s+whale|'
                r'whale|porpoise|dugong|manatee|sea\s+otter|'
                r'caretta\s+caretta|chelonia\s+mydas|monachus\s+monachus)\b',
                re.IGNORECASE
            ),
            # Seabirds
            re.compile(
                r'\b(?P<species>seabird|albatross|petrel|cormorant|gannet|puffin|tern|'
                r'shearwater|guillemot|razorbill|kittiwake|skua|fulmar|osprey)\b',
                re.IGNORECASE
            ),
            # Well-known marine scientific names (safe binomials)
            re.compile(
                r'\b(?P<scientific_name>Posidonia\s+oceanica|Cymodocea\s+nodosa|'
                r'Zostera\s+marina|Caulerpa\s+taxifolia|Caulerpa\s+cylindracea|'
                r'Caretta\s+caretta|Chelonia\s+mydas|Monachus\s+monachus|'
                r'Tursiops\s+truncatus|Delphinus\s+delphis|Stenella\s+coeruleoalba|'
                r'Phocoena\s+phocoena|Balaenoptera\s+physalus|'
                r'Thunnus\s+thynnus|Thunnus\s+alalunga|Xiphias\s+gladius|'
                r'Dicentrarchus\s+labrax|Sparus\s+aurata|Mullus\s+barbatus|'
                r'Engraulis\s+encrasicolus|Sardina\s+pilchardus|Scomber\s+scombrus|'
                r'Merluccius\s+merluccius|Solea\s+solea|'
                r'Mytilus\s+galloprovincialis|Crassostrea\s+gigas|'
                r'Paracentrotus\s+lividus|Octopus\s+vulgaris|'
                r'Hippocampus\s+(?:hippocampus|guttulatus)|'
                r'Pinna\s+nobilis|Lithophaga\s+lithophaga|'
                r'Corallium\s+rubrum|Cladocora\s+caespitosa)\b',
                re.UNICODE
            ),
            # Additional well-known marine scientific names
            re.compile(
                r'\b(?P<scientific_name>Dugong\s+dugon|Halodule\s+uninervis|Halophila\s+ovalis|'
                r'Thalassia\s+hemprichii|Enhalus\s+acoroides|Syringodium\s+isoetifolium|'
                r'Pecten\s+maximus|Ostrea\s+edulis|Ruditapes\s+decussatus|'
                r'Nephrops\s+norvegicus|Homarus\s+gammarus|Panulirus\s+argus|'
                r'Lophius\s+piscatorius|Gadus\s+morhua|Clupea\s+harengus|'
                r'Pleuronectes\s+platessa|Scophthalmus\s+maximus|'
                r'Carcharodon\s+carcharias|Cetorhinus\s+maximus|Prionace\s+glauca|'
                r'Squalus\s+acanthias|Raja\s+clavata|Dasyatis\s+pastinaca|'
                r'Patella\s+(?:vulgata|ferruginea)|Aplysina\s+aerophoba|'
                r'Epinephelus\s+(?:marginatus|aeneus)|Dentex\s+dentex|'
                r'Pagrus\s+pagrus|Pagellus\s+(?:erythrinus|bogaraveo)|'
                r'Diplodus\s+(?:sargus|vulgaris|annularis))\b',
                re.UNICODE
            ),
            # Seagrass / marine plants / invertebrates
            re.compile(
                r'\b(?P<species>seagrass|posidonia|zostera|cymodocea|caulerpa|kelp|'
                r'mangrove|coral|sponge|sea\s+fan|gorgonian|'
                r'phytoplankton|zooplankton|benthic\s+(?:fauna|community|organisms)|'
                r'cetacean|pinniped|elasmobranch)\b',
                re.IGNORECASE
            ),
        ]

    def extract(self, text: str, page_texts: Dict[int, str],
                doc_type: DocumentType) -> List[SpeciesExtraction]:
        """Extract species from text"""
        results: List[SpeciesExtraction] = []
        language = self._get_language(doc_type)

        # Convert written numbers
        converted_text = text
        if self.number_converter:
            converted_text = self.number_converter.convert_text(text, language)

        # Select patterns based on language
        patterns = self.turkish_patterns if language == "turkish" else self.english_patterns

        # Extract species
        for pattern in patterns:
            for match in pattern.finditer(converted_text):
                result = self._process_match(match, converted_text, text, page_texts, language, doc_type)
                if result:
                    results.append(result)

        return self._deduplicate(results)

    def _process_match(self, match: re.Match, converted_text: str, original_text: str,
                       page_texts: Dict[int, str], language: str,
                       doc_type: DocumentType) -> Optional[SpeciesExtraction]:
        """Process a species match"""
        try:

            # Skip bibliography and garbled text
            if self._should_skip_match(converted_text, match.start(), match.group(0), category="species"):
                return None
            groups = match.groupdict()
            sentence, context = self._get_sentence_context(converted_text, match.start(), match.end())

            # Parse species details early for blacklist check
            species_name = groups.get('species', '').strip() if groups.get('species') else None
            scientific_name = groups.get('scientific_name', '').strip() if groups.get('scientific_name') else None

            # Blacklist check for scientific names
            if scientific_name and not species_name:
                parts = scientific_name.split()
                if len(parts) != 2 or len(parts[0]) < 3 or len(parts[1]) < 3:
                    return None
                first_word = parts[0].lower()
                second_word = parts[1].lower()
                if first_word in self.SCIENTIFIC_NAME_BLACKLIST:
                    return None
                # Second word blacklist - common non-species words
                second_word_blacklist = {
                    'analysis', 'curation', 'acquisition', 'administration',
                    'review', 'editing', 'draft', 'preparation', 'interpretation',
                    'availability', 'statement', 'importance', 'role',
                    'and', 'the', 'from', 'with', 'for', 'that', 'this',
                    'planning', 'management', 'assessment', 'policy',
                    'framework', 'approach', 'strategy', 'system',
                    'protected', 'clustering', 'refers', 'diversity',
                    'heterogeneity', 'grazing', 'foraging', 'modelling',
                    'modeling', 'suitability', 'species', 'marine',
                    'spatial', 'temporal', 'coastal', 'environmental',
                    'conservation', 'distribution', 'condition', 'conditions',
                    'change', 'changes', 'area', 'areas', 'zone', 'zones',
                    'model', 'models', 'results', 'methods', 'study',
                    'based', 'level', 'value', 'values', 'data',
                    'impact', 'impacts', 'effect', 'effects',
                    'use', 'used', 'using', 'between', 'within',
                }
                if second_word in second_word_blacklist:
                    return None
                # Reject if scientific_name contains newline
                if '\n' in scientific_name or '\r' in scientific_name:
                    return None

            if not species_name and not scientific_name:
                return None

            # Clean legal references
            cleaned_sentence = sentence
            if self.legal_ref_filter:
                cleaned_sentence = self.legal_ref_filter.clean_text(sentence)

            # False positive check
            is_fp, fp_reason = self._is_false_positive(cleaned_sentence, match.group(0), language)
            if is_fp:
                return None

            # Check marine relevance - higher threshold for scientific names
            marine_score = self.fp_filter.get_marine_relevance_score(cleaned_sentence, language)
            if scientific_name and not species_name:
                min_marine_score = 0.15  # Stricter for scientific name patterns
            else:
                min_marine_score = 0.1  # Named species are more reliable

            if marine_score < min_marine_score:
                return None

            display_name = species_name or scientific_name or match.group(0)
            common_name = groups.get('common', '').strip() if groups.get('common') else None
            protection_status = groups.get('status', '') if groups.get('status') else None

            # Extract activity context
            activity_context = self._extract_activity_context(context, language)

            # Extract legal reference
            legal_ref = self._extract_legal_reference(context, language)

            # Find page number
            page_num = self._find_page_number(match.start(), page_texts)

            # Calculate confidence
            confidence = self._calculate_confidence(
                marine_score, bool(scientific_name), bool(protection_status)
            )

            return SpeciesExtraction(
                species_name=display_name[:100],
                scientific_name=scientific_name,
                common_name=common_name,
                protection_status=protection_status,
                activity_context=activity_context,
                legal_reference=legal_ref,
                context=context[:200],
                exact_text=match.group(0),
                page_number=page_num,
                confidence=confidence,
                marine_relevance=marine_score
            )

        except Exception as e:
            logger.warning(f"Error processing species match: {e}")
            return None

    def _extract_activity_context(self, context: str, language: str) -> Optional[str]:
        """Extract activity context related to species"""
        if language == 'turkish':
            patterns = [
                r'(?:avlan|balıkçılık|koruma|üretim|yetiştirme)',
            ]
        else:
            patterns = [
                r'(?:fishing|hunting|protection|conservation|aquaculture|farming)',
            ]

        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE | re.UNICODE)
            if match:
                start = max(0, match.start() - 20)
                end = min(len(context), match.end() + 20)
                return context[start:end].strip()

        return None

    def _extract_legal_reference(self, context: str, language: str) -> Optional[str]:
        """Extract legal reference from context"""
        if language == 'turkish':
            pattern = r'\d+\s*sayılı\s*(?:kanun|yönetmelik|tüzük)'
        else:
            pattern = r'(?:Act|Law|Regulation)\s+(?:No\.\s*)?\d+'

        match = re.search(pattern, context, re.IGNORECASE | re.UNICODE)
        if match:
            return match.group(0)
        return None

    def _calculate_confidence(self, marine_score: float, has_scientific_name: bool,
                             has_protection_status: bool) -> float:
        """Calculate confidence score"""
        base_confidence = 0.6

        if marine_score > 0.3:
            base_confidence += 0.1
        if has_scientific_name:
            base_confidence += 0.2
        if has_protection_status:
            base_confidence += 0.1

        return min(base_confidence, 1.0)
