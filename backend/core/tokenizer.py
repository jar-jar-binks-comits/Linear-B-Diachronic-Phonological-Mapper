"""
Linear B Tokenizer
Handles authentic tablet text with proper delimiters and logograms
"""

import re
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

class TokenType(Enum):
    SYLLABOGRAM = "syllabogram"
    LOGOGRAM = "logogram"
    NUMBER = "number"
    WORD_DIVIDER = "word_divider"
    LINE_BREAK = "line_break"
    UNKNOWN = "unknown"

@dataclass
class Token:
    char: str
    type: TokenType
    position: int
    
    def __repr__(self):
        return f"Token({self.char!r}, {self.type.name}, pos={self.position})"

class LinearBTokenizer:
    # Unicode ranges
    SYLLABOGRAM_RANGE = (0x10000, 0x1007F)  # Linear B Syllabary
    LOGOGRAM_RANGE = (0x10080, 0x100FA)     # Linear B Ideograms
    
    # Specific delimiters found on tablets
    WORD_DIVIDER = '\u2E31'  # ⸱ (raised dot, common on tablets)
    VERTICAL_BAR = '\U00010100'  # 𐄀 (sentence/phrase divider)
    DOUBLE_VERTICAL = '\U00010101'  # 𐄁 (major break)
    
    def __init__(self):
        self.delimiter_chars = {
            self.WORD_DIVIDER,
            self.VERTICAL_BAR,
            self.DOUBLE_VERTICAL,
            ' ',  # Modern transcription spaces
            '\n',
            '\t'
        }
    
    def is_syllabogram(self, char: str) -> bool:
        """Check if character is a Linear B syllabogram"""
        if not char:
            return False
        code = ord(char)
        return self.SYLLABOGRAM_RANGE[0] <= code <= self.SYLLABOGRAM_RANGE[1]
    
    def is_logogram(self, char: str) -> bool:
        """Check if character is a Linear B ideogram/logogram"""
        if not char:
            return False
        code = ord(char)
        return self.LOGOGRAM_RANGE[0] <= code <= self.LOGOGRAM_RANGE[1]
    
    def is_delimiter(self, char: str) -> bool:
        """Check if character is a word/phrase delimiter"""
        return char in self.delimiter_chars
    
    def tokenize(self, text: str) -> List[Token]:
        """
        Tokenize Linear B text into syllabograms, logograms, and delimiters
        
        Args:
            text: Raw Linear B text with Unicode characters
            
        Returns:
            List of Token objects with type classification
        """
        tokens = []
        
        for i, char in enumerate(text):
            if self.is_syllabogram(char):
                tokens.append(Token(char, TokenType.SYLLABOGRAM, i))
            
            elif self.is_logogram(char):
                tokens.append(Token(char, TokenType.LOGOGRAM, i))
            
            elif char == '\n':
                tokens.append(Token(char, TokenType.LINE_BREAK, i))
            
            elif self.is_delimiter(char):
                tokens.append(Token(char, TokenType.WORD_DIVIDER, i))
            
            elif char.isdigit():
                tokens.append(Token(char, TokenType.NUMBER, i))
            
            else:
                # Unknown character - preserve but mark
                tokens.append(Token(char, TokenType.UNKNOWN, i))
        
        return tokens
    
    def segment_words(self, text: str) -> List[List[Token]]:
        """
        Segment text into words (sequences of syllabograms between delimiters)
        
        Returns:
            List of word-token-lists
        """
        tokens = self.tokenize(text)
        words = []
        current_word = []
        
        for token in tokens:
            if token.type == TokenType.SYLLABOGRAM:
                current_word.append(token)
            
            elif token.type in (TokenType.WORD_DIVIDER, TokenType.LINE_BREAK):
                if current_word:
                    words.append(current_word)
                    current_word = []
            
            elif token.type == TokenType.LOGOGRAM:
                # Logograms are standalone or terminate words
                if current_word:
                    words.append(current_word)
                    current_word = []
                words.append([token])  # Logogram as single-token word
            
            elif token.type == TokenType.NUMBER:
                # Numbers typically follow logograms - attach to previous word if exists
                if words and words[-1][-1].type == TokenType.LOGOGRAM:
                    words[-1].append(token)
                else:
                    words.append([token])
        
        if current_word:
            words.append(current_word)
        
        return words
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize Linear B text for processing
        - Replace various space characters with standard space
        - Standardize delimiters
        """
        # Replace various Unicode spaces
        text = re.sub(r'[\u00A0\u2000-\u200B\u202F\u205F\u3000]', ' ', text)
        
        # Normalize multiple spaces
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
    
    def get_word_strings(self, text: str) -> List[str]:
        """
        Extract just the syllabogram sequences as strings
        Useful for feeding to transcriber
        """
        words = self.segment_words(text)
        return [''.join(token.char for token in word 
                       if token.type == TokenType.SYLLABOGRAM) 
                for word in words if any(t.type == TokenType.SYLLABOGRAM for t in word)]


def test_tokenizer():
    """Test with authentic Linear B examples"""
    print("="*60)
    print("LINEAR B TOKENIZER TEST")
    print("="*60)
    
    tokenizer = LinearBTokenizer()
    
    # Test 1: Simple word
    test1 = "𐀷𐀙𐀏"  # wa-na-ka
    print(f"\nTest 1: {test1}")
    tokens = tokenizer.tokenize(test1)
    print(f"Tokens: {tokens}")
    words = tokenizer.segment_words(test1)
    print(f"Words: {len(words)} word(s)")
    
    # Test 2: Multiple words with space
    test2 = "𐀷𐀙𐀏 𐀡𐀴𐀛𐀊"  # wa-na-ka po-ti-ni-ja
    print(f"\nTest 2: {test2}")
    word_strings = tokenizer.get_word_strings(test2)
    print(f"Extracted words: {word_strings}")
    print(f"Word count: {len(word_strings)}")
    
    # Test 3: With vertical bar delimiter
    test3 = "𐀷𐀙𐀏𐄁𐀡𐀴𐀛𐀊"  # Using proper tablet delimiter
    print(f"\nTest 3: {test3}")
    word_strings = tokenizer.get_word_strings(test3)
    print(f"Extracted words: {word_strings}")
    
    # Test 4: Mixed content (syllabograms + logogram + number)
    # Simulating: "wa-na-ka [MAN-logogram] 5"
    test4 = "𐀷𐀙𐀏 𐂀 5"  # 𐂀 is a commodity ideogram
    print(f"\nTest 4: {test4}")
    tokens = tokenizer.tokenize(test4)
    print(f"Token types: {[t.type.name for t in tokens]}")
    words = tokenizer.segment_words(test4)
    print(f"Segmented: {len(words)} segments")
    
    print("\n" + "="*60)
    print(f"Tokenizer loaded successfully")
    print("="*60)


if __name__ == "__main__":
    test_tokenizer()