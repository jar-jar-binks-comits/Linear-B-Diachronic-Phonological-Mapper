// API Configuration
const API_BASE = 'http://localhost:5000/api';

// DOM Elements
const inputTextarea = document.getElementById('linearb-input');
const analyzeBtn = document.getElementById('analyze-btn');
const clearBtn = document.getElementById('clear-btn');
const resultsSection = document.getElementById('results');
const resultsContainer = document.getElementById('results-container');
const exampleChips = document.querySelectorAll('.example-chip');

// Paradigm elements
const paradigmWord = document.getElementById('paradigm-word');
const generateParadigmBtn = document.getElementById('generate-paradigm-btn');
const paradigmResults = document.getElementById('paradigm-results');

// Lexicon elements
const loadLexiconBtn = document.getElementById('load-lexicon-btn');
const lexiconContainer = document.getElementById('lexicon-container');

// Sound changes elements
const loadChangesBtn = document.getElementById('load-changes-btn');
const changesContainer = document.getElementById('changes-container');

// Event Listeners
analyzeBtn.addEventListener('click', analyzeText);
clearBtn.addEventListener('click', clearInput);

exampleChips.forEach(chip => {
    chip.addEventListener('click', (e) => {
        inputTextarea.value = e.target.dataset.text;
        analyzeText();
    });
});

if (generateParadigmBtn) {
    generateParadigmBtn.addEventListener('click', generateParadigm);
}

if (loadLexiconBtn) {
    loadLexiconBtn.addEventListener('click', loadLexicon);
}

if (loadChangesBtn) {
    loadChangesBtn.addEventListener('click', loadSoundChanges);
}

// Keyboard shortcuts
inputTextarea.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        analyzeText();
    }
});

// Main Analysis Function
async function analyzeText() {
    const text = inputTextarea.value.trim();
    
    console.log('Input text:', text);
    console.log('Text length:', text.length);
    console.log('Character codes:', [...text].map(c => c.charCodeAt(0).toString(16)));

    if (!text) {
        alert('Please enter Linear B text');
        return;
    }
    
    analyzeBtn.classList.add('loading');
    analyzeBtn.textContent = 'Analyzing...';
    analyzeBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/full_analysis`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        
        if (!response.ok) throw new Error('Analysis failed');
        
        const data = await response.json();
        console.log('API response:', data);
        displayResultsCompact(data.results);
        
    } catch (error) {
        console.error('Analysis error:', error);
        resultsContainer.innerHTML = `
            <div style="padding: 2rem; text-align: center; color: var(--red);">
                <h3>Analysis Failed</h3>
                <p>Please check your input and try again.</p>
            </div>
        `;
        resultsSection.style.display = 'block';
    } finally {
        analyzeBtn.classList.remove('loading');
        analyzeBtn.textContent = 'Analyze';
        analyzeBtn.disabled = false;
    }
}

// Display Results 
function displayResultsCompact(results) {
    resultsContainer.innerHTML = '';
    resultsSection.style.display = 'block';
    
    if (!results || results.length === 0) {
        resultsContainer.innerHTML = '<p style="text-align:center;padding:2rem;color:var(--base01);">No results found.</p>';
        return;
    }
    
    results.forEach((word, index) => {
        const card = document.createElement('div');
        card.className = 'result-card';
        
        // Header
        let html = `
            <div class="result-header">
                <div class="word-display">
                    <span class="linear-b-large">${word.original}</span>
                    <span class="transliteration">${word.transliteration}</span>
                    <span class="phonetic">/${word.phonetic}/</span>
                </div>
            </div>
        `;
        
        // Info grid
        html += '<div class="info-grid">';
        
        // Morphology
        if (word.morphology) {
            html += `
                <div class="info-card">
                    <h4>Morphology</h4>
                    <div class="info-value">${word.morphology.stem} + ${word.morphology.ending || '∅'}</div>
                    <div class="info-secondary">
                        ${word.morphology.case ? word.morphology.case : ''} 
                        ${word.morphology.number ? word.morphology.number : ''}
                        ${word.morphology.confidence ? `(${(word.morphology.confidence * 100).toFixed(0)}%)` : ''}
                    </div>
                </div>
            `;
        }
        
        // Classical
        if (word.diachronic) {
            html += `
                <div class="info-card" style="border-left-color: var(--blue);">
                    <h4>Classical Greek</h4>
                    <div class="info-value">${word.diachronic.classical}</div>
                    <div class="info-secondary">${word.diachronic.meaning}</div>
                </div>
            `;
        }
        
        html += '</div>';
        
        // PIE Etymology (if available)
        if (word.diachronic && word.diachronic.pie_root) {
            html += `
                <div class="pie-compact">
                    <h4 style="font-size: 0.75rem; color: var(--base01); text-transform: uppercase; margin-bottom: 0.5rem;">Proto-Indo-European</h4>
                    <div class="pie-root">${word.diachronic.pie_root}</div>
                    ${word.diachronic.pie_meaning ? `<div class="pie-meaning">"${word.diachronic.pie_meaning}"</div>` : ''}
                    ${word.diachronic.cognates ? `
                    <div class="cognates-compact">
                        ${Object.entries(word.diachronic.cognates).map(([lang, form]) => 
                            `<span class="cognate-tag">${lang}: ${form}</span>`
                        ).join('')}
                    </div>` : ''}
                </div>
            `;
        }
        
        // Timeline (if diachronic stages available)
        if (word.diachronic && word.diachronic.stages && word.diachronic.stages.length > 0) {
            html += '<div class="timeline-compact">';
            word.diachronic.stages.slice(0, 4).forEach((stage, i) => {
                html += `
                    <div class="timeline-stage">
                        <div class="stage-form">${stage.form}</div>
                        <div class="stage-period">${stage.period.split(' ')[0]}</div>
                    </div>
                `;
            });
            html += '</div>';
        }
        
        card.innerHTML = html;
        resultsContainer.appendChild(card);
        
        // Auto-populate paradigm generator with first word
        if (index === 0 && paradigmWord) {
            paradigmWord.value = word.transliteration;
        }
    });
}

// Paradigm Generator
async function generateParadigm() {
    const word = paradigmWord.value.trim();
    
    if (!word) {
        alert('Enter a word transliteration');
        return;
    }
    
    generateParadigmBtn.textContent = 'Generating...';
    generateParadigmBtn.disabled = true;
    
    try {
        let response = await fetch(`${API_BASE}/generate/${word}`);
        
        if (!response.ok) {
            response = await fetch(`${API_BASE}/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    stem: word.replace(/-/g, ''),
                    pos: 'noun',
                    declension: 'o_stem_masculine',
                    gender: 'masculine'
                })
            });
        }
        
        const data = await response.json();
        displayParadigmCompact(data);
        
    } catch (error) {
        console.error('Paradigm generation error:', error);
        paradigmResults.innerHTML = '<p style="color: var(--red); font-size: 0.85rem;">Generation failed</p>';
        paradigmResults.style.display = 'block';
    } finally {
        generateParadigmBtn.textContent = 'Generate';
        generateParadigmBtn.disabled = false;
    }
}

function displayParadigmCompact(data) {
    paradigmResults.style.display = 'block';
    
    let html = '<div class="paradigm-mini">';
    
    // Stats
    html += `
        <div class="paradigm-stat">
            <span>Total forms:</span>
            <strong>${data.total_forms || data.total}</strong>
        </div>
        <div class="paradigm-stat">
            <span>Attested:</span>
            <strong style="color: var(--green);">${data.attested || 0}</strong>
        </div>
        <div class="paradigm-stat">
            <span>Coverage:</span>
            <strong>${data.coverage || '0%'}</strong>
        </div>
    `;
    
    // Show first 8 forms
    const forms = data.generated_paradigm || data.forms || [];
    html += '<div style="margin-top: 1rem; max-height: 300px; overflow-y: auto;">';
    
    forms.slice(0, 10).forEach(form => {
        const attestedClass = form.attested ? 'attested' : '';
        html += `
            <div class="form-mini ${attestedClass}">
                <div style="font-weight: 600; color: var(--cyan);">${form.form}</div>
                <div style="font-size: 0.75rem; color: var(--base01);">
                    ${form.case || ''} ${form.number || ''}
                    ${form.attested ? '<span style="color: var(--green);">✓</span>' : ''}
                </div>
            </div>
        `;
    });
    
    if (forms.length > 10) {
        html += `<div style="text-align: center; padding: 0.5rem; color: var(--base01); font-size: 0.75rem;">+${forms.length - 10} more forms</div>`;
    }
    
    html += '</div></div>';
    paradigmResults.innerHTML = html;
}

// Load Lexicon
async function loadLexicon() {
    if (lexiconContainer.style.display === 'block') {
        lexiconContainer.style.display = 'none';
        loadLexiconBtn.textContent = 'Browse';
        return;
    }
    
    loadLexiconBtn.textContent = 'Loading...';
    
    try {
        const response = await fetch(`${API_BASE}/lexicon`);
        const data = await response.json();
        
        let html = '<div class="lexicon-mini">';
        
        // Sort alphabetically
        const sortedWords = data.words.sort((a, b) => 
            a.transliteration.localeCompare(b.transliteration)
        );
        
        sortedWords.forEach(word => {
            html += `
                <div class="lex-item-mini" data-word="${word.transliteration}">
                    <div class="lex-trans-mini">${word.transliteration}</div>
                    <div class="lex-meaning-mini">${word.meaning}</div>
                    ${word.pie_root ? `<div style="font-size: 0.7rem; color: var(--violet); margin-top: 0.2rem;">${word.pie_root}</div>` : ''}
                </div>
            `;
        });
        
        html += '</div>';
        lexiconContainer.innerHTML = html;
        
        // Add click handlers
        lexiconContainer.querySelectorAll('.lex-item-mini').forEach(item => {
            item.addEventListener('click', () => {
                const word = item.dataset.word;
                inputTextarea.value = word;
                analyzeText();
            });
        });
        
        lexiconContainer.style.display = 'block';
        loadLexiconBtn.textContent = `Hide (${data.words.length})`;
        
    } catch (error) {
        console.error('Failed to load lexicon:', error);
        loadLexiconBtn.textContent = 'Browse';
    }
}

// Load Sound Changes
async function loadSoundChanges() {
    if (changesContainer.style.display === 'block') {
        changesContainer.style.display = 'none';
        loadChangesBtn.textContent = 'View Rules';
        return;
    }
    
    loadChangesBtn.textContent = 'Loading...';
    
    try {
        const response = await fetch(`${API_BASE}/sound_changes`);
        const data = await response.json();
        
        let html = '<div style="max-height: 400px; overflow-y: auto;">';
        
        data.changes.forEach((change, index) => {
            html += `
                <div class="change-mini">
                    <div class="change-name-mini">${index + 1}. ${change.name}</div>
                    <div class="change-rule-mini">${change.source} → ${change.target}</div>
                    <div style="font-size: 0.7rem; color: var(--base01); margin-top: 0.3rem;">${change.period}</div>
                </div>
            `;
        });
        
        html += '</div>';
        changesContainer.innerHTML = html;
        changesContainer.style.display = 'block';
        loadChangesBtn.textContent = `Hide (${data.changes.length})`;
        
    } catch (error) {
        console.error('Failed to load sound changes:', error);
        loadChangesBtn.textContent = 'View Rules';
    }
}

// Clear Input
function clearInput() {
    inputTextarea.value = '';
    resultsSection.style.display = 'none';
    resultsContainer.innerHTML = '';
    if (paradigmResults) {
        paradigmResults.style.display = 'none';
    }
}

// Load Syllabary
async function loadSyllabary() {
    try {
        const response = await fetch(`${API_BASE.replace('/api', '')}/data/syllabary.json`);
        const text = await response.text(); // Get as text first
        const data = JSON.parse(text); // Then parse
        const grid = document.getElementById('syllabary-grid');
        
        if (!grid) return;
        
        // Sort by transliteration
        const sortedSigns = Object.entries(data.signs).sort((a, b) => 
            a[1].transliteration.localeCompare(b[1].transliteration)
        );
        
        sortedSigns.forEach(([unicodeChar, info]) => {
            const btn = document.createElement('button');
            btn.className = 'syllabary-sign';
            btn.type = 'button'; // Important: prevent form submission
            
            // Store the character directly in dataset
            btn.dataset.char = unicodeChar;
            
            btn.innerHTML = `
                <span class="sign">${unicodeChar}</span>
                <span class="label">${info.transliteration}</span>
            `;
            btn.title = `${info.transliteration} - Click to insert`;
            
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                
                // Get the character from the button's dataset
                const charToInsert = btn.dataset.char;
                
                // Get current cursor position
                const start = inputTextarea.selectionStart;
                const end = inputTextarea.selectionEnd;
                const currentValue = inputTextarea.value;
                
                // Insert character at cursor position
                inputTextarea.value = 
                    currentValue.substring(0, start) + 
                    charToInsert + 
                    currentValue.substring(end);
                
                // Move cursor after inserted character
                const newPosition = start + charToInsert.length;
                inputTextarea.selectionStart = newPosition;
                inputTextarea.selectionEnd = newPosition;
                
                // Focus back on textarea
                inputTextarea.focus();
            });
            
            grid.appendChild(btn);
        });
        
        console.log(`Loaded ${sortedSigns.length} syllabary signs`);
        
    } catch (error) {
        console.error('Failed to load syllabary:', error);
    }
}

// Initialise
document.addEventListener('DOMContentLoaded', () => {
    loadSyllabary();
    console.log('Linear B Diachronic Mapper initialized');
    console.log('Keyboard shortcut: Ctrl/Cmd + Enter to analyze');
});