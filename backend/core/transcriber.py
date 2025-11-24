"""
Linear B Transcriber v2
Uses tokenizer for proper text segmentation
"""

import json
import os
from typing import List, Dict, Optional
from .tokenizer import LinearBTokenizer, TokenType

class LinearBTranscriber:
    def __init__(self, data_dir: str = "data"):
        """Initialize with syllabary data and tokenizer"""
        syllabary_path = os.path.join(data_dir, "syllabary.json")
        
        with open(syllabary_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.syllabary = data['signs']
        
        self.tokenizer = LinearBTokenizer()
    
    def transcribe_sign(self, sign: str) -> Optional[str]:
        """Get transliteration for single syllabogram"""
        if sign in self.syllabary:
            return self.syllabary[sign]['transliteration']
        return None
    
    def transcribe_word(self, word_tokens: List) -> str:
        """
        Transcribe a segmented word (list of tokens) to transliteration
        
        Args:
            word_tokens: List of Token objects from tokenizer
            
        Returns:
            Hyphen-separated transliteration (e.g. "wa-na-ka")
        """
        syllables = []
        
        for token in word_tokens:
            if token.type == TokenType.SYLLABOGRAM:
                trans = self.transcribe_sign(token.char)
                if trans:
                    syllables.append(trans)
                else:
                    syllables.append(f"[?{token.char}]")
            
            elif token.type == TokenType.LOGOGRAM:
                syllables.append(f"*{ord(token.char):04X}")  # Show as Unicode point
        
        return "-".join(syllables) if syllables else ""
    
    def transcribe_text(self, text: str) -> List[Dict]:
        """
        Transcribe full Linear B text with word segmentation
        
        Returns:
            List of dicts with 'original' and 'transliteration' for each word
        """
        normalized = self.tokenizer.normalize_text(text)
        word_segments = self.tokenizer.segment_words(normalized)
        
        print(f"[TRANSCRIBER] Received text: {text!r}")
        print(f"[TRANSCRIBER] Normalised: {normalized!r}")
        print(f"[TRANSCRIBER] Segment into {len(word_segments)} words")
        
        results = []
        for word_tokens in word_segments:
            original = ''.join(t.char for t in word_tokens)
            transliteration = self.transcribe_word(word_tokens)
            
            print(f"[TRANSCRIBER] Word: {original!r} → {transliteration!r}")
            
            if transliteration:
                results.append({
                    'original': original,
                    'transliteration': transliteration,
                    'token_count': len([t for t in word_tokens 
                                       if t.type == TokenType.SYLLABOGRAM])
                })
        print(f"[TRANSCRIBER] Returning {len(results)} results")
        return results
    
    def get_phonetic_form(self, transliteration: str) -> str:
        """
        Convert transliteration to approximate phonetic form
        Simple version - handles basic sound values
        """
        # Remove hyphens
        clean = transliteration.replace("-", "")
        
        # Apply basic phonetic correspondences
        phonetic = clean
        phonetic = phonetic.replace("nw", "nʷ")  # Labialized n
        phonetic = phonetic.replace("kw", "kʷ")  # Labiovelar
        phonetic = phonetic.replace("qu", "kʷ")
        phonetic = phonetic.replace("ph", "pʰ")  # Aspirate
        phonetic = phonetic.replace("th", "tʰ")
        phonetic = phonetic.replace("kh", "kʰ")
        
        return phonetic


def test_transcriber():
    """Test updated transcriber with tokenizer"""
    print("="*60)
    print("LINEAR B TRANSCRIBER V2 TEST")
    print("="*60)
    
    transcriber = LinearBTranscriber()
    
    # Test 1
    test1 = "𐀷𐀙𐀏"
    print(f"\nTest 1: {test1}")
    results = transcriber.transcribe_text(test1)
    for r in results:
        print(f"  {r['original']} → {r['transliteration']}")
        print(f"  Phonetic: {transcriber.get_phonetic_form(r['transliteration'])}")
    
    # Test 2: Multiple words
    test2 = "𐀷𐀙𐀏 𐀡𐀴𐀛𐀊"
    print(f"\nTest 2: {test2}")
    results = transcriber.transcribe_text(test2)
    for r in results:
        print(f"  {r['original']} → {r['transliteration']}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    test_transcriber()