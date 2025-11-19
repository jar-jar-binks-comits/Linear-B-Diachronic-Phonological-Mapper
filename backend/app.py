"""
Linear B Analysis Tool - Flask Backend
Integrates tokenizer, transcriber, morphology, and phonology engines
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import sys

# Add core modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from core.tokenizer import LinearBTokenizer
from core.transcriber import LinearBTranscriber
from core.morphology import MorphologicalAnalyzer
from core.phonology import PhonologyEngine

app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')
CORS(app)

# Initialize engines
tokenizer = LinearBTokenizer()
transcriber = LinearBTranscriber(data_dir='data')
morphology = MorphologicalAnalyzer(data_dir='data')
phonology = PhonologyEngine(data_dir='data')


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
    
    # Transcribe
    results = transcriber.transcribe_text(text)
    
    # Add phonetic forms
    for result in results:
        result['phonetic'] = transcriber.get_phonetic_form(result['transliteration'])
    
    return jsonify({'words': results})


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    Full morphological analysis of a word
    
    Request: {"word": "wa-na-ka-te"}
    Response: {
        "analyses": [
            {
                "stem": "wanak",
                "ending": "te",
                "case": "dative",
                "number": "singular",
                "confidence": 0.9
            }
        ]
    }
    """
    data = request.get_json()
    word = data.get('word', '')
    
    if not word:
        return jsonify({'error': 'No word provided'}), 400
    
    # Analyze
    analyses = morphology.segment_word(word)
    
    # Convert to dicts
    result = {
        'word': word,
        'analyses': [a.to_dict() for a in analyses[:3]]  # Top 3
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
    
    # Get diachronic path
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
    Complete analysis pipeline: transcribe → morphology → diachronic
    
    Request: {"text": "𐀷𐀙𐀏"}
    Response: {
        "transcription": {...},
        "morphology": {...},
        "diachronic": {...}
    }
    """
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    results = []
    
    # Transcribe
    transcriptions = transcriber.transcribe_text(text)
    
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
        
        # Diachronic (if word in lexicon)
        try:
            # Try to get classical form from lexicon
            word_data = morphology.lexicon.get(trans['transliteration'])
            if word_data and 'classical_greek' in word_data:
                myc_form = word_data.get('reconstruction', trans['transliteration'].replace('-', ''))
                clas_form = word_data['classical_greek']
                
                path = phonology.apply_changes(myc_form, clas_form)
                word_analysis['diachronic'] = {
                    'classical': clas_form,
                    'meaning': word_data.get('meaning', ''),
                    'stages': path.to_dict()['stages'][:3],  # Show first 3 stages
                    'total_changes': len(path.changes_applied)
                }
        except:
            pass
        
        results.append(word_analysis)
    
    return jsonify({'results': results})


@app.route('/api/lexicon', methods=['GET'])
def get_lexicon():
    """Return all words in lexicon"""
    words = []
    for trans, data in morphology.lexicon.items():
        words.append({
            'transliteration': trans,
            'meaning': data.get('meaning', ''),
            'classical': data.get('classical_greek', ''),
            'pos': data.get('pos', 'unknown')
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


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'operational',
        'engines': {
            'tokenizer': True,
            'transcriber': True,
            'morphology': True,
            'phonology': True
        },
        'lexicon_size': len(morphology.lexicon),
        'sound_rules': len(phonology.rules)
    })


if __name__ == '__main__':
    print("="*70)
    print("LINEAR B ANALYSIS TOOL - Starting Server")
    print("="*70)
    print(f"Lexicon: {len(morphology.lexicon)} words")
    print(f"Phonological rules: {len(phonology.rules)}")
    print(f"Morphological endings: {len(morphology.ending_map)}")
    print("="*70)
    print("\nServer running at http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    
    app.run(debug=True, port=5000)