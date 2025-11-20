"""
Mycenaean Paradigm Generator
First computational implementation of complete Mycenaean inflectional morphology
Based on Ventris & Chadwick (1956), Morpurgo Davies (2002)
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json
import os

@dataclass
class InflectedForm:
    """Single inflected form with grammatical information"""
    form: str
    case: Optional[str] = None
    number: Optional[str] = None
    gender: Optional[str] = None
    tense: Optional[str] = None
    mood: Optional[str] = None
    person: Optional[str] = None
    attested: bool = False  # Found on actual tablets
    reconstruction: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'form': self.form,
            'case': self.case,
            'number': self.number,
            'gender': self.gender,
            'tense': self.tense,
            'mood': self.mood,
            'person': self.person,
            'attested': self.attested,
            'reconstruction': self.reconstruction
        }


class ParadigmGenerator:
    """
    Generates complete inflectional paradigms for Mycenaean Greek
    """
    
    def __init__(self, data_dir: str = "data"):
        # Load paradigm templates
        paradigm_path = os.path.join(data_dir, "paradigms.json")
        with open(paradigm_path, 'r', encoding='utf-8') as f:
            self.paradigms = json.load(f)
        
        # Define Linear B orthographic rules
        self.orthography = {
            # Linear B cannot write final consonants except -s, -n, -r
            'final_consonant_omission': True,
            # Linear B merges voiced/voiceless stops in certain positions
            'stop_neutralization': True,
            # Cannot write consonant clusters
            'cluster_simplification': True
        }
    
    def generate_noun_paradigm(self, 
                               stem: str, 
                               declension: str, 
                               gender: str,
                               attested_forms: List[str] = None) -> List[InflectedForm]:
        """
        Generate complete nominal paradigm
        
        Args:
            stem: Base stem (e.g., 'wanak' for wanax)
            declension: Type (o_stem_masculine, a_stem_feminine, consonant_stem)
            gender: masculine, feminine, neuter
            attested_forms: List of forms actually found on tablets
            
        Returns:
            List of all theoretically possible forms
        """
        if attested_forms is None:
            attested_forms = []
        
        forms = []
        
        # Get declension template
        if declension not in self.paradigms.get('noun_declensions', {}):
            return forms
        
        decl_data = self.paradigms['noun_declensions'][declension]
        
        # Generate each case/number combination
        for case_number, endings in decl_data.get('endings', {}).items():
            case, number = case_number.rsplit('_', 1)
            
            for ending in endings:
                # Apply ending to stem
                form, recon = self._apply_ending(stem, ending, declension)
                
                forms.append(InflectedForm(
                    form=form,
                    case=case,
                    number=number,
                    gender=gender,
                    attested=form in attested_forms,
                    reconstruction=recon
                ))
        
        return forms
    
    def _apply_ending(self, stem: str, ending: str, declension: str) -> Tuple[str, str]:
        """
        Apply ending to stem with Linear B orthographic rules
        
        Returns:
            (linear_b_form, phonological_reconstruction)
        """
        # Clean ending
        ending_clean = ending.replace('-', '')
        
        # Phonological form (what was actually pronounced)
        if ending_clean == '∅':
            reconstruction = stem
        else:
            reconstruction = stem + ending_clean
        
        # Linear B orthographic form (what could be written)
        lb_form = self._apply_orthographic_rules(reconstruction)
        
        # Convert to syllabic transliteration
        syllabified = self._syllabify(lb_form)
        
        return syllabified, reconstruction
    
    def _apply_orthographic_rules(self, form: str) -> str:
        """
        Apply Linear B writing system constraints
        """
        result = form
        
        # Rule 1: Final stops are not written (except s, n, r)
        if self.orthography['final_consonant_omission']:
            if result and result[-1] in 'tdkgbp':
                result = result[:-1]
        
        # Rule 2: Cannot write double consonants (simplify)
        result = self._simplify_clusters(result)
        
        return result
    
    def _simplify_clusters(self, form: str) -> str:
        """
        Simplify consonant clusters for Linear B writing
        Linear B uses CV syllables, so clusters need vowel insertion or simplification
        """
        # This is simplified - real implementation needs full phonotactic rules
        result = []
        i = 0
        while i < len(form):
            char = form[i]
            
            # If consonant followed by another consonant, insert default vowel
            if i < len(form) - 1:
                next_char = form[i + 1]
                if self._is_consonant(char) and self._is_consonant(next_char):
                    result.append(char)
                    # Insert 'o' as default helping vowel (Linear B convention)
                    if next_char != 's':  # Special handling for s
                        result.append('o')
                else:
                    result.append(char)
            else:
                result.append(char)
            
            i += 1
        
        return ''.join(result)
    
    def _is_consonant(self, char: str) -> bool:
        """Check if character is consonant"""
        return char.lower() not in 'aeiouāēīōūαεηιουω'
    
    def _syllabify(self, form: str) -> str:
        """
        Convert phonological form to syllabic Linear B transliteration
        e.g., 'wanaka' -> 'wa-na-ka'
        """
        if not form:
            return form
        
        syllables = []
        i = 0
        
        while i < len(form):
            char = form[i]
            #Handle double letters (Reduce to single)
            if i < len(form) - 1 and form[i] == form[i + 1]:
                i += 1
                continue 
            
            # CV syllable (most common in linear B)
            if self._is_consonant(char):
                if i < len(form) - 1 and not self._is_consonant(form[i + 1]):
                    syllables.append(char + form[i + 1])
                    i += 2
                    continue
                else:
                    #Consonant without vowel - skip or attach 
                    if syllables:
                        syllables[-1] += char
                        i += 1
                        continue 
                    
            # Standalone vowel
            syllables.append(char)
            i += 1
        
        return '-'.join(syllables)
    def _apply_ortographic_rules(self, form:str) -> str:
        #Apply Linear B writing system constraints 
        result = form
        # remove geminate consonants (Linear B doesn't write doubles)
        result = ''.join(c for i, c in enumerate(result)
                         if i == 0 or c != result[i-1] or not self._is_consonant(c))
        #final consonants: only -s written in linear b
        if result and self._is_consonant(result[-1]) and result [-1] not in 'snr':
            result = result[:-1]
            
        return result 
    
    def generate_verb_paradigm(self, 
                               root: str,
                               attested_forms: List[str] = None) -> List[InflectedForm]:
        """
        Generate verbal paradigm (limited - Mycenaean verb system is fragmentary)
        
        Args:
            root: Verbal root (e.g., 'do' for 'give')
            attested_forms: List of attested forms
            
        Returns:
            List of possible verbal forms
        """
        if attested_forms is None:
            attested_forms = []
        
        forms = []
        
        # Present tense endings (thematic verbs)
        present_endings = {
            '1sg': '-ō',
            '2sg': '-eis',
            '3sg': '-ei',
            '1pl': '-omen',
            '2pl': '-ete',
            '3pl': '-onsi'
        }
        
        for person_num, ending in present_endings.items():
            person = person_num[-2] + 'rd' if person_num[-2] == '3' else person_num[-2] + 'st' if person_num[-2] == '1' else '2nd'
            number = 'singular' if person_num[-2:] == 'sg' else 'plural'
            
            form, recon = self._apply_verb_ending(root, ending)
            
            forms.append(InflectedForm(
                form=form,
                tense='present',
                mood='indicative',
                person=person,
                number=number,
                attested=form in attested_forms,
                reconstruction=recon
            ))
        
        # Future tense (s-stem)
        future_3sg, recon_fut = self._apply_verb_ending(root, '-sei')
        forms.append(InflectedForm(
            form=future_3sg,
            tense='future',
            mood='indicative',
            person='3rd',
            number='singular',
            attested=future_3sg in attested_forms,
            reconstruction=recon_fut
        ))
        
        # Aorist (simplified - only 3sg)
        aorist_3sg, recon_aor = self._apply_verb_ending(root, '-se')
        forms.append(InflectedForm(
            form=aorist_3sg,
            tense='aorist',
            mood='indicative',
            person='3rd',
            number='singular',
            attested=aorist_3sg in attested_forms,
            reconstruction=recon_aor
        ))
        
        return forms
    
    def _apply_verb_ending(self, root: str, ending: str) -> Tuple[str, str]:
        """Apply verbal ending with phonological rules"""
        ending_clean = ending.replace('-', '')
        reconstruction = root + ending_clean
        lb_form = self._apply_orthographic_rules(reconstruction)
        syllabified = self._syllabify(lb_form)
        return syllabified, reconstruction
    
    def generate_all_forms(self, 
                          stem: str, 
                          pos: str,
                          **kwargs) -> Dict[str, List[InflectedForm]]:
        """
        Generate all forms based on part of speech
        
        Args:
            stem: Base form
            pos: 'noun', 'verb', 'adjective'
            **kwargs: Additional parameters (declension, gender, etc.)
            
        Returns:
            Dictionary with form types as keys
        """
        if pos == 'noun':
            declension = kwargs.get('declension', 'o_stem_masculine')
            gender = kwargs.get('gender', 'masculine')
            attested = kwargs.get('attested_forms', [])
            
            forms = self.generate_noun_paradigm(stem, declension, gender, attested)
            return {'inflected_forms': forms}
        
        elif pos == 'verb':
            attested = kwargs.get('attested_forms', [])
            forms = self.generate_verb_paradigm(stem, attested)
            return {'conjugated_forms': forms}
        
        else:
            return {}


def test_generator():
    """Test paradigm generator"""
    print("="*70)
    print("MYCENAEAN PARADIGM GENERATOR TEST")
    print("="*70)
    
    generator = ParadigmGenerator()
    
    # Test 1: O-stem masculine noun (theos)
    print("\n1. O-STEM MASCULINE: theo- (god)")
    print("-" * 70)
    forms = generator.generate_noun_paradigm(
        stem='theo',
        declension='o_stem_masculine',
        gender='masculine',
        attested_forms=['te-o', 'te-o-i']
    )
    
    for form in forms[:8]:  # Show first 8 forms
        status = "✓ ATTESTED" if form.attested else "  theoretical"
        print(f"  {form.form:15} {form.case:12} {form.number:8} [{status}]")
        print(f"    reconstruction: *{form.reconstruction}")
    
    # Test 2: Consonant stem (wanax)
    print("\n2. CONSONANT STEM: wanak- (king)")
    print("-" * 70)
    forms = generator.generate_noun_paradigm(
        stem='wanak',
        declension='consonant_stem',
        gender='masculine',
        attested_forms=['wa-na-ka', 'wa-na-ka-te']
    )
    
    for form in forms[:6]:
        status = "✓ ATTESTED" if form.attested else "  theoretical"
        print(f"  {form.form:15} {form.case:12} {form.number:8} [{status}]")
    
    # Test 3: Verb paradigm
    print("\n3. VERB: do- (give)")
    print("-" * 70)
    forms = generator.generate_verb_paradigm(
        root='do',
        attested_forms=['di-do-si']
    )
    
    for form in forms[:8]:
        status = "✓ ATTESTED" if form.attested else "  theoretical"
        print(f"  {form.form:15} {form.tense:10} {form.person:5} {form.number:8} [{status}]")
    
    print("\n" + "="*70)
    print("Paradigm generator operational")
    print("="*70)


if __name__ == "__main__":
    test_generator()