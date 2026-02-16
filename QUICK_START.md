## MSP Extractor Modular - Quick Start Guide

### What You Have Now

**COMPLETE MODULAR ARCHITECTURE** with:
- ✓ 17 corrected dataclass definitions
- ✓ Base extractor class
- ✓ 1 fully working extractor (Distance)
- ✓ 16 stub extractors ready to implement
- ✓ Configuration module
- ✓ Clear project structure

### What Works Right Now

**DistanceExtractor** is fully functional and extracts:
- Distance measurements (100 metre, 50-100 km)
- Buffer zones
- Setbacks
- Qualifiers (minimum, maximum, approximately)
- Reference points (from coastline, from baseline)
- Activity context (fishing, shipping, aquaculture)

**Results so far:**
- 124 distance extractions from Turkish legal documents
- 2,183 distance extractions from Q1 scientific papers

### What's Next - 3 Options

#### Option 1: Conference Paper (Distance Only) - 2-3 Weeks
**Best if you have very limited time**

1. Use existing distance results (already extracted)
2. Manually validate 50-100 samples
3. Write conference paper focused on distance/buffer zones only
4. Submit to conference

**Pros:** Ready now, minimal work
**Cons:** Limited scope (1/17 categories)

#### Option 2: Implement 5-6 Key Categories - 4-5 Weeks
**Balanced approach for conference**

1. Complete utility modules (Week 1)
2. Implement these extractors (Weeks 2-3):
   - Penalty (fines, imprisonment)
   - Temporal (seasonal restrictions)
   - Environmental (water quality, noise limits)
   - Prohibition (bans, restrictions)
   - Protected Area (MPAs, conservation zones)
   - Species (protected species mentions)
3. Run on full corpus (Week 4)
4. Validate + write paper (Week 5)

**Pros:** Rich dataset, publishable, doable in time
**Cons:** Requires focused work

#### Option 3: Complete All 17 Categories - 3 Months
**For journal publication quality**

Systematically implement all extractors

**Pros:** Complete system, Q1 journal ready
**Cons:** Too long for immediate conference deadline

### Recommended: Option 2 (5-6 Categories)

This gives you:
- **Diverse extraction types**: Distances, penalties, restrictions, species
- **Conference-publishable**: Enough variety to be interesting
- **Achievable**: 4-5 weeks of focused work
- **Legal + Scientific**: Works on both document types

---

## Step-by-Step: Implementing Your Next Extractor

### Example: Let's Implement PenaltyExtractor

#### Step 1: Review the Dataclass
Open: `data_structures/extraction_models.py`

Look at `PenaltyExtraction`:
```python
@dataclass
class PenaltyExtraction:
    penalty_type: str  # "fine", "imprisonment", "license_revocation"
    amount: Optional[float] = None
    currency: Optional[str] = None
    duration: Optional[str] = None  # for imprisonment
    violation: Optional[str] = None
    legal_reference: Optional[str] = None
    ...
```

#### Step 2: Study the Template
Open: `extractors/distance_extractor.py`

Key sections:
- `_compile_patterns()`: Where regex patterns are defined
- `extract()`: Main extraction logic
- `_process_match()`: How to handle each regex match
- Helper methods: `_parse_value()`, `_validate_value()`, `_normalize_unit()`

#### Step 3: Add Turkish Patterns
Open: `extractors/penalty_extractor.py`

Replace the stub with real patterns:
```python
def _compile_patterns(self):
    """Compile penalty patterns"""
    self.turkish_patterns = [
        # "100 bin lira ceza"
        re.compile(
            r'(?P<amount>\d+(?:[.,]\d+)?)\s*'
            r'(?P<unit>bin|milyon)?\s*'
            r'(?P<currency>lira|TL)\s*'
            r'(?P<type>ceza|para\s*cezası|idari\s*para\s*cezası)',
            re.IGNORECASE | re.UNICODE
        ),

        # "1 yıldan 3 yıla kadar hapis"
        re.compile(
            r'(?P<min>\d+)\s*(?P<min_unit>yıl|ay|gün)dan\s+'
            r'(?P<max>\d+)\s*(?P<max_unit>yıl|ay|gün)a?\s*kadar\s*'
            r'(?P<type>hapis|hapis\s*cezası)',
            re.IGNORECASE | re.UNICODE
        ),

        # "6 ay hapis cezası"
        re.compile(
            r'(?P<duration>\d+)\s*(?P<unit>yıl|ay|gün)\s*'
            r'(?P<type>hapis|hapis\s*cezası)',
            re.IGNORECASE | re.UNICODE
        ),
    ]
```

#### Step 4: Add English Patterns
```python
    self.english_patterns = [
        # "fine of $10,000"
        re.compile(
            r'(?P<type>fine)\s+of\s+'
            r'(?P<currency>\$|USD|EUR)?\s*'
            r'(?P<amount>\d+(?:,\d{3})*(?:\.\d+)?)',
            re.IGNORECASE
        ),

        # "imprisonment for 1-3 years"
        re.compile(
            r'(?P<type>imprisonment|prison)\s+for\s+'
            r'(?P<min>\d+)\s*(?:to|-)\s*(?P<max>\d+)\s*'
            r'(?P<unit>years?|months?|days?)',
            re.IGNORECASE
        ),
    ]
```

#### Step 5: Implement extract() Method
```python
def extract(self, text: str, page_texts: Dict[int, str],
            doc_type: DocumentType) -> List[PenaltyExtraction]:
    """Extract penalties from text"""
    results: List[PenaltyExtraction] = []
    language = self._get_language(doc_type)

    # Select patterns
    patterns = self.turkish_patterns if language == "turkish" else self.english_patterns

    # Extract
    for pattern in patterns:
        for match in pattern.finditer(text):
            result = self._process_match(match, text, page_texts, language, doc_type)
            if result:
                results.append(result)

    return self._deduplicate(results)
```

#### Step 6: Implement _process_match()
```python
def _process_match(self, match, text, page_texts, language, doc_type):
    """Process a penalty match"""
    try:
        groups = match.groupdict()
        sentence, context = self._get_sentence_context(text, match.start(), match.end())

        # Parse amount
        amount = None
        if 'amount' in groups and groups['amount']:
            amount = float(groups['amount'].replace(',', '').replace('.', ''))
            # Handle "bin" (thousand), "milyon" (million)
            if groups.get('unit') == 'bin':
                amount *= 1000
            elif groups.get('unit') == 'milyon':
                amount *= 1000000

        # Parse penalty type
        penalty_type = self._parse_type(groups.get('type', ''), language)

        # Parse currency
        currency = groups.get('currency', 'TL' if language == 'turkish' else 'USD')

        # Parse duration (for imprisonment)
        duration = None
        if 'duration' in groups and groups['duration']:
            duration = f"{groups['duration']} {groups.get('unit', '')}"
        elif 'min' in groups and 'max' in groups:
            duration = f"{groups['min']}-{groups['max']} {groups.get('min_unit', '')}"

        # Find violation description
        violation = self._extract_violation(context, language)

        # Page number
        page_num = self._find_page_number(match.start(), page_texts)

        return PenaltyExtraction(
            penalty_type=penalty_type,
            amount=amount,
            currency=currency,
            duration=duration,
            violation=violation,
            context=context[:200],
            exact_text=match.group(0),
            page_number=page_num,
            confidence=0.8,
            marine_relevance=0.5  # Calculate properly
        )

    except Exception as e:
        logger.warning(f"Error processing penalty: {e}")
        return None
```

#### Step 7: Test It
Create `test_penalty.py`:
```python
from extractors.penalty_extractor import PenaltyExtractor
from core.enums import DocumentType

# Minimal setup for testing
class MockKeywords:
    ACTIVITIES = {}
    DISTANCE_TERMS = {'reference_points': {'turkish': {}, 'english': {}}}

class MockSegmenter:
    def segment(self, text):
        return [text]

class MockFPFilter:
    def is_false_positive(self, *args):
        return False, ""
    def get_marine_relevance_score(self, *args):
        return 0.5

# Test
extractor = PenaltyExtractor(MockKeywords(), MockSegmenter(), MockFPFilter())

test_text = "Bu fiili işleyene 100 bin lira idari para cezası verilir."
results = extractor.extract(test_text, {1: test_text}, DocumentType.LEGAL_TURKISH)

print(f"Found {len(results)} penalties:")
for r in results:
    print(f"  - {r.amount} {r.currency} ({r.penalty_type})")
    print(f"    Text: {r.exact_text}")
```

#### Step 8: Run the Test
```bash
cd C:\Users\ahk79\Downloads\msp_extractor_modular
python test_penalty.py
```

Expected output:
```
Found 1 penalties:
  - 100000.0 TL (fine)
    Text: 100 bin lira idari para cezası
```

---

## Your Action Plan for Next Week

### Day 1-2: Create Utility Modules
You need these before implementing more extractors. Extract them from the main script:
1. `utils/sentence_segmenter.py`
2. `utils/legal_reference_filter.py`
3. `utils/false_positive_filter.py`

### Day 3: Implement PenaltyExtractor
Follow the guide above. Test with Turkish law PDFs.

### Day 4: Implement TemporalExtractor
Similar process, focus on dates and seasons.

### Day 5: Implement EnvironmentalExtractor
Focus on numerical thresholds (dB, pH, temperature).

### Weekend: Run on Full Corpus
Process all legal docs + Q1 papers with your 4 working extractors.

---

## Questions?

**Q: Do I need to implement all 17?**
A: No! For a conference paper, 5-6 diverse categories is excellent.

**Q: Can I test before implementing all utilities?**
A: Yes! Use mock objects (see test example above) for quick testing.

**Q: What if a category has no results?**
A: That's fine! Report it: "We found 0 species mentions in legal docs, suggesting laws focus on spatial regulations rather than species-specific protections."

**Q: Should I fix all bugs in the old code first?**
A: No! This modular version IS the fix. Work here, not on the old file.

---

## Ready to Start?

**Your first task:** Create the utility modules

I can help you extract these from the main script. Should we start with that?
