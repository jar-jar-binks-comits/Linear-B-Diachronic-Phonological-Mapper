"""
Diachronic Phonology Engine
Traces sound changes from Mycenaean to Classical Greek
"""

import json
import os
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class ChangeType(Enum):
    LOSS = "loss"
    MERGER = "merger"
    SPLIT = "split"
    LENITION = "lenition"
    COMPENSATORY_LENGTHENING = "compensatory_lengthening"
    ASSIMILATION = "assimilation"

@dataclass
class SoundChange:
    """Represents a single phonological change"""
    name: str
    source: str  # Input sound/pattern
    target: str  # Output sound/pattern
    environment: str  # Phonological context (# = word boundary, V = vowel, C = consonant)
    period: str  # Time period (e.g., "1200-800 BCE")
    change_type: ChangeType
    description: str
    examples: List[Tuple[str, str]] = None  # (before, after) pairs
    
    def __post_init__(self):
        if self.examples is None:
            self.examples = []

@dataclass
class DiachronicPath:
    """Complete evolution path from Mycenaean to Classical"""
    mycenaean: str
    classical: str
    intermediate_stages: List[Tuple[str, str, str]]  # (form, period, change_applied)
    changes_applied: List[SoundChange]
    
    def to_dict(self) -> Dict:
        return {
            'mycenaean': self.mycenaean,
            'classical': self.classical,
            'stages': [
                {
                    'form': stage[0],
                    'period': stage[1],
                    'change': stage[2]
                }
                for stage in self.intermediate_stages
            ],
            'total_changes': len(self.changes_applied)
        }


class PhonologyEngine:
    def __init__(self, data_dir: str = "data"):
        """Load phonological rules"""
        rules_path = os.path.join(data_dir, "phonological_rules.json")
        
        if os.path.exists(rules_path):
            with open(rules_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.rules = self._load_rules(data)
        else:
            # Use hardcoded rules if file doesn't exist yet
            self.rules = self._default_rules()
    
    def _default_rules(self) -> List[SoundChange]:
        """Hardcoded default sound changes (Mycenaean → Classical)"""
        return [
            # Digamma loss (most important)
            SoundChange(
                name="Initial digamma loss",
                source="w-",
                target="∅",
                environment="#_",
                period="1200-800 BCE",
                change_type=ChangeType.LOSS,
                description="Loss of initial /w/ (digamma) in most dialects except Aeolic",
                examples=[("wanaks", "anaks"), ("woikos", "oikos"), ("wergon", "ergon")]
            ),
            SoundChange(
                name="Intervocalic digamma loss",
                source="-w-",
                target="∅",
                environment="V_V",
                period="1000-700 BCE",
                change_type=ChangeType.LOSS,
                description="Loss of /w/ between vowels, often with compensatory lengthening",
                examples=[("newos", "neos"), ("korwa", "kore")]
            ),
            
            # Labiovelar changes
            SoundChange(
                name="Labiovelar to labial",
                source="kʷ",
                target="p",
                environment="_e,i",
                period="1400-1200 BCE (Pre-Mycenaean)",
                change_type=ChangeType.SPLIT,
                description="Labiovelar *kʷ becomes /p/ before front vowels",
                examples=[("kʷetwores", "petwores → tessares")]
            ),
            SoundChange(
                name="Labiovelar to velar",
                source="kʷ",
                target="k/t",
                environment="_a,o,u",
                period="1400-1200 BCE",
                change_type=ChangeType.SPLIT,
                description="Labiovelar *kʷ becomes /k/ or /t/ before back vowels (dialectal variation)",
                examples=[("kʷo", "ko → po (Attic tis)")]
            ),
            
            # Sibilant changes
            SoundChange(
                name="Intervocalic *s loss",
                source="-s-",
                target="-h-",
                environment="V_V",
                period="1200-800 BCE",
                change_type=ChangeType.LENITION,
                description="Intervocalic *s weakens to /h/, eventually lost with compensatory lengthening",
                examples=[("genesos", "geneos → genous")]
            ),
            
            # Cluster simplifications
            SoundChange(
                name="Final stop loss",
                source="-t,-d,-k,-g",
                target="∅",
                environment="_#",
                period="1200-1000 BCE",
                change_type=ChangeType.LOSS,
                description="Loss of final stops in word-final position",
                examples=[("wanakt", "wanaks → anax")]
            ),
            SoundChange(
                name="ti → si",
                source="ti",
                target="si",
                environment="_V",
                period="800-400 BCE (Attic)",
                change_type=ChangeType.ASSIMILATION,
                description="Palatalization: /ti/ becomes /si/ before vowels (Attic-Ionic)",
                examples=[("potiʰon", "posithon → Poseidon")]
            ),
            
            # Vowel changes
            SoundChange(
                name="Quantitative metathesis",
                source="VRV (short V + resonant + long V)",
                target="VRV (long V + resonant + short V)",
                environment="syllable",
                period="1000-800 BCE",
                change_type=ChangeType.MERGER,
                description="Shift in vowel quantity across resonants",
                examples=[("poləwos", "poleos → poleos")]
            ),
            SoundChange(
                name="Compensatory lengthening",
                source="Vs → V:",
                target="long vowel",
                environment="V_C",
                period="1200-800 BCE",
                change_type=ChangeType.COMPENSATORY_LENGTHENING,
                description="Vowel lengthens when following consonant is lost",
                examples=[("esmi", "ēmi"), ("ansa", "āsa")]
            ),
            
            # Aspiration
            SoundChange(
                name="Grassmann's Law",
                source="aspirate...aspirate → stop...aspirate",
                target="C",
                environment="aspiration dissimilation",
                period="Pre-Classical",
                change_type=ChangeType.ASSIMILATION,
                description="Dissimilation of aspirates (first loses aspiration)",
                examples=[("tʰrikʰ-", "trikʰ- (thrix)"), ("pʰatʰer", "pater")]
            )
        ]
    
    def _load_rules(self, data: Dict) -> List[SoundChange]:
        """Load rules from JSON data"""
        rules = []
        for rule_data in data.get('sound_changes', []):
            rule = SoundChange(
                name=rule_data['name'],
                source=rule_data['source'],
                target=rule_data['target'],
                environment=rule_data.get('environment', ''),
                period=rule_data.get('period', 'Unknown'),
                change_type=ChangeType[rule_data.get('type', 'LOSS').upper()],
                description=rule_data.get('description', ''),
                examples=rule_data.get('examples', [])
            )
            rules.append(rule)
        return rules
    
    def apply_changes(self, mycenaean_form: str, classical_form: str) -> DiachronicPath:
        """
        Determine which sound changes apply between Mycenaean and Classical forms
        """
        # Normalize forms
        myc = mycenaean_form.replace('-', '').lower()
        clas = classical_form.lower()
        
        applied_changes = []
        stages = [(myc, "1450-1200 BCE", "Mycenaean Greek (attested)")]
        current_form = myc
        
        # Check each rule
        for rule in self.rules:
            if self._rule_applies(current_form, classical_form, rule):
                # Apply the change
                new_form = self._apply_rule(current_form, rule)
                if new_form != current_form:
                    applied_changes.append(rule)
                    stages.append((new_form, rule.period, rule.name))
                    current_form = new_form
        
        # Add classical stage
        stages.append((clas, "800-400 BCE", "Classical Greek"))
        
        return DiachronicPath(
            mycenaean=myc,
            classical=clas,
            intermediate_stages=stages,
            changes_applied=applied_changes
        )
    
    def _rule_applies(self, current: str, target: str, rule: SoundChange) -> bool:
        """Determine if a rule should apply"""
        source = rule.source.replace('-', '')
        
        # Simple pattern matching
        if rule.environment == "#_":  # Initial position
            return current.startswith(source) and not target.startswith(source)
        elif rule.environment == "_#":  # Final position
            return current.endswith(source) and not target.endswith(source)
        elif rule.environment == "V_V":  # Intervocalic
            return source in current and self._is_intervocalic(current, source)
        else:
            return source in current and source not in target
    
    def _is_intervocalic(self, word: str, segment: str) -> bool:
        """Check if segment appears between vowels"""
        vowels = set('aeiouāēīōū')
        idx = word.find(segment)
        if idx > 0 and idx + len(segment) < len(word):
            before = word[idx - 1]
            after = word[idx + len(segment)]
            return before in vowels and after in vowels
        return False
    
    def _apply_rule(self, form: str, rule: SoundChange) -> str:
        """Apply a phonological rule to a form"""
        source = rule.source.replace('-', '')
        target = rule.target.replace('-', '')
        
        if target == '∅':  # Deletion
            if rule.environment == "#_":
                if form.startswith(source):
                    return form[len(source):]
            elif rule.environment == "_#":
                if form.endswith(source):
                    return form[:-len(source)]
            else:
                return form.replace(source, '')
        else:
            return form.replace(source, target)
        
        return form
    
    def get_changes_by_type(self, change_type: ChangeType) -> List[SoundChange]:
        """Get all rules of a specific type"""
        return [rule for rule in self.rules if rule.change_type == change_type]
    
    def explain_divergence(self, myc: str, clas: str) -> List[str]:
        """Generate human-readable explanation of changes"""
        path = self.apply_changes(myc, clas)
        explanations = []
        
        for change in path.changes_applied:
            explanations.append(f"• {change.name}: {change.description}")
        
        return explanations


def test_phonology():
    """Test phonology engine"""
    print("="*70)
    print("DIACHRONIC PHONOLOGY ENGINE TEST")
    print("="*70)
    
    engine = PhonologyEngine()
    
    # Test cases
    test_pairs = [
        ("wanaks", "ἄναξ (anax)"),
        ("korwa", "κόρη (kore)"),
        ("woikos", "οἶκος (oikos)"),
        ("theos", "θεός (theos)")
    ]
    
    for myc, clas in test_pairs:
        print(f"\n{myc} → {clas}")
        print("-" * 70)
        
        path = engine.apply_changes(myc, clas)
        
        print("Evolutionary stages:")
        for i, (form, period, change) in enumerate(path.intermediate_stages, 1):
            print(f"  {i}. {form:15} ({period})")
            if i < len(path.intermediate_stages):
                print(f"     └─ {change}")
        
        explanations = engine.explain_divergence(myc, clas)
        if explanations:
            print("\nSound changes:")
            for exp in explanations:
                print(f"  {exp}")
    
    print("\n" + "="*70)
    print(f"Total phonological rules loaded: {len(engine.rules)}")
    print("="*70)


if __name__ == "__main__":
    test_phonology()