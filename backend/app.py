"""
Linear B Analysis Tool - Flask Backend
Integrates tokenizer, transcriber, morphology, phonology, and generator engines
"""
import sys
import io

# Force UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# Add core modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from core.tokenizer import LinearBTokenizer
from core.transcriber import LinearBTranscriber
from core.morphology import MorphologicalAnalyzer
from core.phonology import PhonologyEngine
from core.generator import ParadigmGenerator

app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')
CORS(app)

# Initialise engines
tokenizer = LinearBTokenizer()
transcriber = LinearBTranscriber(data_dir='data')
morphology = MorphologicalAnalyzer(data_dir='data')
phonology = PhonologyEngine(data_dir='data')
generator = ParadigmGenerator(data_dir='data')


@app.route('/')
def index():
    """Serve main interface"""
    return render_template('index.html')


@app.route('/api/transcribe', methods=['POST'])
def transcribe():
    """
    Transcribe Linear B text to transliteration
    
    Request: {"text": "𐀷𐀙𐀏"}
    Response: {
        "words": [
            {
                "original": "𐀷𐀙𐀏",
                "transliteration": "wa-na-ka",
                "phonetic": "wanaka"
            }
        ]
    }
    """
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    results = transcriber.transcribe_text(text)
    
    for result in results:
        result['phonetic'] = transcriber.get_phonetic_form(result['transliteration'])
    
    return jsonify({'words': results})


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    Full morphological analysis of a word
    
    Request: {"word": "wa-na-ka-te"}
    Response: {
        "analyses": [...]
    }
    """
    data = request.get_json()
    word = data.get('word', '')
    
    if not word:
        return jsonify({'error': 'No word provided'}), 400
    
    analyses = morphology.segment_word(word)
    
    result = {
        'word': word,
        'analyses': [a.to_dict() for a in analyses[:3]]
    }
    
    return jsonify(result)


@app.route('/api/diachronic', methods=['POST'])
def diachronic_analysis():
    """
    Trace sound changes from Mycenaean to Classical
    
    Request: {"mycenaean": "wanaks", "classical": "anax"}
    Response: {
        "stages": [...],
        "changes": [...],
        "explanations": [...]
    }
    """
    data = request.get_json()
    myc = data.get('mycenaean', '')
    clas = data.get('classical', '')
    
    if not myc or not clas:
        return jsonify({'error': 'Both forms required'}), 400
    
    path = phonology.apply_changes(myc, clas)
    explanations = phonology.explain_divergence(myc, clas)
    
    return jsonify({
        'mycenaean': path.mycenaean,
        'classical': path.classical,
        'stages': path.to_dict()['stages'],
        'total_changes': len(path.changes_applied),
        'changes': [
            {
                'name': c.name,
                'description': c.description,
                'period': c.period,
                'type': c.change_type.value
            }
            for c in path.changes_applied
        ],
        'explanations': explanations
    })


@app.route('/api/full_analysis', methods=['POST'])
def full_analysis():
    """
    Complete analysis pipeline: transcribe → morphology → diachronic → PIE
    
    Request: {"text": "𐀷𐀙𐀏"}
    Response: {
        "results": [...]
    }
    """
    data = request.get_json()
    text = data.get('text', '')
    
    print(f"Received text: {text!r}")
    print(f"Text length: {len(text)}")
    print(f"Characters: {[c for c in text]}")
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    results = []
    
    transcriptions = transcriber.transcribe_text(text)
    
    print(f"Transcribed {len(transcriptions)} words")
    for trans in transcriptions:
        print(f"  - {trans}")
    
    for trans in transcriptions:
        word_analysis = {
            'original': trans['original'],
            'transliteration': trans['transliteration'],
            'phonetic': transcriber.get_phonetic_form(trans['transliteration'])
        }
        
        # Morphology
        morph_analyses = morphology.segment_word(trans['transliteration'])
        if morph_analyses:
            word_analysis['morphology'] = morph_analyses[0].to_dict()
        
        # Diachronic + PIE
        try:
            word_data = morphology.lexicon.get(trans['transliteration'])
            if word_data and 'classical_greek' in word_data:
                myc_form = word_data.get('reconstruction', trans['transliteration'].replace('-', ''))
                clas_form = word_data['classical_greek']
                
                path = phonology.apply_changes(myc_form, clas_form)
                word_analysis['diachronic'] = {
                    'classical': clas_form,
                    'meaning': word_data.get('meaning', ''),
                    'stages': path.to_dict()['stages'][:4],
                    'total_changes': len(path.changes_applied),
                    'pie_root': word_data.get('pie_root'),
                    'pie_meaning': word_data.get('pie_meaning'),
                    'cognates': word_data.get('cognates')
                }
        except Exception as e:
            print(f"Diachronic analysis error: {e}")
        
        results.append(word_analysis)
    
    return jsonify({'results': results})


@app.route('/api/generate', methods=['POST'])
def generate_paradigm():
    """
    Generate complete inflectional paradigm
    
    Request: {
        "stem": "theo",
        "pos": "noun",
        "declension": "o_stem_masculine",
        "gender": "masculine"
    }
    """
    data = request.get_json()
    stem = data.get('stem', '')
    pos = data.get('pos', 'noun')
    
    if not stem:
        return jsonify({'error': 'No stem provided'}), 400
    
    result = generator.generate_all_forms(
        stem=stem,
        pos=pos,
        declension=data.get('declension', 'o_stem_masculine'),
        gender=data.get('gender', 'masculine'),
        attested_forms=data.get('attested_forms', [])
    )
    
    all_forms = []
    for form_list in result.values():
        all_forms.extend([f.to_dict() for f in form_list])
    
    attested_count = sum(1 for f in all_forms if f['attested'])
    
    return jsonify({
        'stem': stem,
        'pos': pos,
        'forms': all_forms,
        'total': len(all_forms),
        'attested': attested_count,
        'coverage': f"{(attested_count/len(all_forms)*100):.1f}%" if all_forms else "0%"
    })


@app.route('/api/generate/<word>', methods=['GET'])
def generate_from_lexicon(word):
    """
    Generate paradigm for word in lexicon
    
    Example: GET /api/generate/wa-na-ka
    """
    if word not in morphology.lexicon:
        return jsonify({'error': 'Word not in lexicon'}), 404
    
    word_data = morphology.lexicon[word]
    stem = word_data.get('stem', word.replace('-', ''))
    pos = word_data.get('pos', 'noun')
    
    # Get ALL attested forms from lexicon
    attested_forms = word_data.get('attested_forms', [])
    if word not in attested_forms:
        attested_forms.append(word)
    
    result = generator.generate_all_forms(
        stem=stem,
        pos=pos,
        declension=word_data.get('declension', 'consonant_stem', 'o_stem_masculine'),
        gender=word_data.get('gender', 'masculine'),
        attested_forms=attested_forms
    )
    
    all_forms = []
    for form_list in result.values():
        all_forms.extend([f.to_dict() for f in form_list])
    
    attested_count = sum(1 for f in all_forms if f['attested'])
    
    return jsonify({
        'word': word,
        'lemma_data': {
            'meaning': word_data.get('meaning'),
            'classical': word_data.get('classical_greek'),
            'stem': stem,
            'declension': word_data.get('declension'),
            'pie_root': word_data.get('pie_root'),
            'pie_meaning': word_data.get('pie_meaning'),
            'cognates': word_data.get('cognates')
        },
        'generated_paradigm': all_forms,
        'total_forms': len(all_forms),
        'attested': attested_count,
        'coverage': f"{(attested_count/len(all_forms)*100):.1f}%" if all_forms else "0%"
    })


@app.route('/api/lexicon', methods=['GET'])
def get_lexicon():
    """Return all words in lexicon"""
    words = []
    for trans, data in morphology.lexicon.items():
        words.append({
            'transliteration': trans,
            'meaning': data.get('meaning', ''),
            'classical': data.get('classical_greek', ''),
            'pos': data.get('pos', 'unknown'),
            'pie_root': data.get('pie_root', '')
        })
    return jsonify({'words': words})


@app.route('/api/sound_changes', methods=['GET'])
def get_sound_changes():
    """Return all phonological rules"""
    changes = [
        {
            'name': rule.name,
            'source': rule.source,
            'target': rule.target,
            'environment': rule.environment,
            'period': rule.period,
            'type': rule.change_type.value,
            'description': rule.description,
            'examples': rule.examples
        }
        for rule in phonology.rules
    ]
    return jsonify({'changes': changes})


@app.route('/data/syllabary.json')
def serve_syllabary():
    """Serve syllabary data for frontend"""
    import json
    with open('data/syllabary.json', 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'operational',
        'engines': {
            'tokenizer': True,
            'transcriber': True,
            'morphology': True,
            'phonology': True,
            'generator': True
        },
        'lexicon_size': len(morphology.lexicon),
        'sound_rules': len(phonology.rules)
    })


if __name__ == '__main__':
    print("="*70)
    print("LINEAR B DIACHRONIC PHONOLOGICAL MAPPER")
    print("="*70)
    print(f"Lexicon: {len(morphology.lexicon)} words")
    print(f"Phonological rules: {len(phonology.rules)}")
    print(f"Morphological endings: {len(morphology.ending_map)}")
    print("="*70)
    print("\nServer running at http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    
    app.run(debug=True, port=5000)