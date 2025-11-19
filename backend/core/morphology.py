"""
Mycenaean Greek Morphological Analyzer v2
Rule-based segmentation using paradigm tables
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class MorphologicalAnalysis:
    """Result of morphological analysis"""
    transliteration: str
    stem: str
    ending: str
    case: Optional[str] = None
    number: Optional[str] = None
    declension: Optional[str] = None
    confidence: float = 0.0
    notes: List[str] = None
    
    def __post_init__(self):
        if self.notes is None:
            self.notes = []
    
    def to_dict(self) -> Dict:
        return {
            'transliteration': self.transliteration,
            'stem': self.stem,
            'ending': self.ending,
            'case': self.case,
            'number': self.number,
            'declension': self.declension,
            'confidence': self.confidence,
            'notes': self.notes
        }


class MorphologicalAnalyzer:
    def __init__(self, data_dir: str = "data"):
        """Load paradigm tables and lexicon"""
        paradigm_path = os.path.join(data_dir, "paradigms.json")
        lexicon_path = os.path.join(data_dir, "lexicon.json")
        
        with open(paradigm_path, 'r', encoding='utf-8') as f:
            self.paradigms = json.load(f)
        
        with open(lexicon_path, 'r', encoding='utf-8') as f:
            lex_data = json.load(f)
            self.lexicon = lex_data.get('words', {})
        
        # Build reverse lookup: ending → grammatical info
        self.ending_map = self._build_ending_map()
    
    def _build_ending_map(self) -> Dict[str, List[Dict]]:
        """Create lookup table from endings to case/number info"""
        ending_map = {}
        
        # From explicit case_markers section
        for ending, info in self.paradigms.get('case_markers', {}).items():
            clean_ending = ending.replace('-', '')
            if clean_ending not in ending_map:
                ending_map[clean_ending] = []
            ending_map[clean_ending].append(info)
        
        # From declension tables
        for decl_name, decl_data in self.paradigms.get('noun_declensions', {}).items():
            for case_num, endings in decl_data.get('endings', {}).items():
                case, number = case_num.rsplit('_', 1)
                
                for ending in endings:
                    clean_ending = ending.replace('-', '').replace('∅', '')
                    if not clean_ending:
                        continue
                    
                    if clean_ending not in ending_map:
                        ending_map[clean_ending] = []
                    
                    ending_map[clean_ending].append({
                        'case': case,
                        'number': number,
                        'declension': decl_name
                    })
        
        return ending_map
    
    def segment_word(self, transliteration: str) -> List[MorphologicalAnalysis]:
        """
        Attempt to segment word into stem + ending
        Returns list of possible analyses sorted by confidence
        """
        # Remove hyphens for processing
        normalized = transliteration.replace('-', '')
        
        # Check if word is in lexicon first
        if transliteration in self.lexicon:
            return self._analyze_known_word(transliteration, normalized)
        
        # Try to segment unknown word
        return self._segment_unknown_word(normalized)
    
    def _analyze_known_word(self, original: str, normalized: str) -> List[MorphologicalAnalysis]:
        """Handle word that exists in lexicon"""
        word_data = self.lexicon[original]
        
        # If lexicon has stem information, use it
        stem = word_data.get('stem', normalized)
        
        analyses = []
        
        # Try to find ending
        for ending, infos in self.ending_map.items():
            if normalized.endswith(ending) and ending:
                stem_part = normalized[:-len(ending)]
                
                for info in infos:
                    analysis = MorphologicalAnalysis(
                        transliteration=original,
                        stem=stem_part,
                        ending=ending,
                        case=info.get('case'),
                        number=info.get('number'),
                        declension=info.get('declension'),
                        confidence=0.9,  # High confidence for known words
                        notes=[f"Attested in lexicon: {word_data.get('meaning', '')}"]
                    )
                    analyses.append(analysis)
        
        # If no ending found, treat as uninflected/citation form
        if not analyses:
            analyses.append(MorphologicalAnalysis(
                transliteration=original,
                stem=stem,
                ending='',
                case='nominative',
                number='singular',
                confidence=0.8,
                notes=['Citation form (no overt ending)']
            ))
        
        return sorted(analyses, key=lambda x: x.confidence, reverse=True)
    
    def _segment_unknown_word(self, normalized: str) -> List[MorphologicalAnalysis]:
        """Attempt segmentation of unattested word"""
        analyses = []
        
        # Try all known endings from longest to shortest
        endings_by_length = sorted(self.ending_map.items(), 
                                   key=lambda x: len(x[0]), 
                                   reverse=True)
        
        for ending, infos in endings_by_length:
            if normalized.endswith(ending) and ending:
                stem = normalized[:-len(ending)]
                
                # Minimum stem length heuristic
                if len(stem) < 2:
                    continue
                
                for info in infos:
                    # Lower confidence for unknown words
                    confidence = 0.6 if len(ending) >= 2 else 0.4
                    
                    analysis = MorphologicalAnalysis(
                        transliteration=normalized,
                        stem=stem,
                        ending=ending,
                        case=info.get('case'),
                        number=info.get('number'),
                        declension=info.get('declension'),
                        confidence=confidence,
                        notes=['Unattested word - analysis tentative']
                    )
                    analyses.append(analysis)
        
        # If no analysis possible, return unsegmented
        if not analyses:
            analyses.append(MorphologicalAnalysis(
                transliteration=normalized,
                stem=normalized,
                ending='',
                confidence=0.1,
                notes=['Cannot segment - no recognized ending']
            ))
        
        return sorted(analyses, key=lambda x: x.confidence, reverse=True)
    
    def analyze_text(self, words: List[str]) -> List[List[MorphologicalAnalysis]]:
        """Analyze multiple words, return best analysis for each"""
        return [self.segment_word(word) for word in words]


def test_morphology():
    """Test morphological analyzer"""
    print("="*60)
    print("MORPHOLOGICAL ANALYZER TEST")
    print("="*60)
    
    analyzer = MorphologicalAnalyzer()
    
    # Test known words
    test_words = [
        "wa-na-ka",
        "wa-na-ka-te",  # wanax + dative ending
        "te-o",
        "po-ti-ni-ja"
    ]
    
    for word in test_words:
        print(f"\n{word}:")
        analyses = analyzer.segment_word(word)
        
        for i, analysis in enumerate(analyses[:3], 1):  # Show top 3
            print(f"  Analysis {i} (confidence: {analysis.confidence:.2f}):")
            print(f"    Stem: {analysis.stem}")
            print(f"    Ending: -{analysis.ending}" if analysis.ending else "    Ending: (none)")
            if analysis.case:
                print(f"    Case: {analysis.case}, Number: {analysis.number}")
            if analysis.notes:
                print(f"    Notes: {', '.join(analysis.notes)}")
    
    # Test unknown word
    print(f"\n\nUnknown word test: 'ka-ko-de'")
    analyses = analyzer.segment_word("ka-ko-de")
    for analysis in analyses[:2]:
        print(f"  Stem: {analysis.stem}, Ending: -{analysis.ending}")
        print(f"  Case: {analysis.case}, Confidence: {analysis.confidence:.2f}")
    
    print("\n" + "="*60)
    print(f"Loaded {len(analyzer.ending_map)} distinct endings")
    print("="*60)


if __name__ == "__main__":
    test_morphology()