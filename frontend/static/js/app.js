// API base URL
const API_BASE = 'http://localhost:5000/api';

// DOM elements
const inputTextarea = document.getElementById('linearb-input');
const analyzeBtn = document.getElementById('analyze-btn');
const clearBtn = document.getElementById('clear-btn');
const resultsSection = document.getElementById('results');
const resultsContainer = document.getElementById('results-container');
const exampleBtns = document.querySelectorAll('.example-btn');
const loadLexiconBtn = document.getElementById('load-lexicon-btn');
const lexiconContainer = document.getElementById('lexicon-container');
const loadChangesBtn = document.getElementById('load-changes-btn');
const changesContainer = document.getElementById('changes-container');

// Load syllabary on page load
async function loadSyllabary() {
    try {
        const response = await fetch('data/syllabary.json');
        const data = await response.json();
        const grid = document.getElementById('syllabary-grid');
        
        Object.entries(data.signs).forEach(([unicode, info]) => {
            const btn = document.createElement('button');
            btn.className = 'syllabary-sign';
            btn.innerHTML = `
                <span class="sign">${unicode}</span>
                <span class="label">${info.transliteration}</span>
            `;
            btn.addEventListener('click', () => {
                inputTextarea.value += unicode;
                inputTextarea.focus();
            });
            grid.appendChild(btn);
        });
    } catch (error) {
        console.error('Failed to load syllabary:', error);
    }
}

// Call on load
loadSyllabary();

// Event listeners
analyzeBtn.addEventListener('click', analyzeText);
clearBtn.addEventListener('click', clearInput);
exampleBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
        inputTextarea.value = e.target.dataset.text;
        analyzeText();
    });
});
loadLexiconBtn.addEventListener('click', loadLexicon);
loadChangesBtn.addEventListener('click', loadSoundChanges);

// Main analysis function
async function analyzeText() {
    const text = inputTextarea.value.trim();
    
    if (!text) {
        alert('Please enter Linear B text');
        return;
    }
    
    analyzeBtn.classList.add('loading');
    analyzeBtn.textContent = 'Analyzing';
    
    try {
        const response = await fetch(`${API_BASE}/full_analysis`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        
        const data = await response.json();
        displayResults(data.results);
        
    } catch (error) {
        console.error('Analysis error:', error);
        alert('Analysis failed. Check console for details.');
    } finally {
        analyzeBtn.classList.remove('loading');
        analyzeBtn.textContent = 'Analyze';
    }
}

// Display results
function displayResults(results) {
    resultsContainer.innerHTML = '';
    resultsSection.style.display = 'block';
    
    results.forEach(word => {
        const wordDiv = document.createElement('div');
        wordDiv.className = 'word-result';
        
        let html = `
            <div class="word-header">
                <span class="linear-b-text">${word.original}</span>
                <span class="transliteration">${word.transliteration}</span>
                <span class="phonetic">/${word.phonetic}/</span>
            </div>
        `;
        
        html += '<div class="analysis-grid">';
        
        // Morphology
        if (word.morphology) {
            html += `
                <div class="analysis-card">
                    <h4>Morphology</h4>
                    <p><strong>Stem:</strong> ${word.morphology.stem}</p>
                    <p><strong>Ending:</strong> -${word.morphology.ending || '∅'}</p>
                    ${word.morphology.case ? `<p><strong>Case:</strong> ${word.morphology.case}</p>` : ''}
                    ${word.morphology.number ? `<p><strong>Number:</strong> ${word.morphology.number}</p>` : ''}
                    <p><strong>Confidence:</strong> ${(word.morphology.confidence * 100).toFixed(0)}%</p>
                </div>
            `;
        }
        
        // Diachronic
        if (word.diachronic) {
            html += `
                <div class="analysis-card">
                    <h4>Classical Greek</h4>
                    <p><strong>Form:</strong> ${word.diachronic.classical}</p>
                    <p><strong>Meaning:</strong> ${word.diachronic.meaning}</p>
                    <p><strong>Changes:</strong> ${word.diachronic.total_changes} phonological rules</p>
                </div>
            `;
        }
        
        html += '</div>';
        
        // Timeline
        if (word.diachronic && word.diachronic.stages) {
            html += '<div class="stage-timeline">';
            word.diachronic.stages.forEach(stage => {
                html += `
                    <div class="stage">
                        <div class="stage-form">${stage.form}</div>
                        <div class="stage-period">${stage.period}</div>
                        ${stage.change ? `<div class="stage-change">→ ${stage.change}</div>` : ''}
                    </div>
                `;
            });
            html += '</div>';
        }
        
        wordDiv.innerHTML = html;
        resultsContainer.appendChild(wordDiv);
    });
}

// Load lexicon
async function loadLexicon() {
    if (lexiconContainer.style.display === 'block') {
        lexiconContainer.style.display = 'none';
        loadLexiconBtn.textContent = 'Load Full Lexicon';
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/lexicon`);
        const data = await response.json();
        
        lexiconContainer.innerHTML = '<div class="lexicon-grid"></div>';
        const grid = lexiconContainer.querySelector('.lexicon-grid');
        
        data.words.forEach(word => {
            const item = document.createElement('div');
            item.className = 'lexicon-item';
            item.innerHTML = `
                <div class="transliteration">${word.transliteration}</div>
                <div class="meaning">${word.meaning}</div>
                <div class="classical">${word.classical}</div>
            `;
            item.addEventListener('click', () => {
                // Find corresponding Linear B and analyze
                inputTextarea.value = word.transliteration;
            });
            grid.appendChild(item);
        });
        
        lexiconContainer.style.display = 'block';
        loadLexiconBtn.textContent = 'Hide Lexicon';
        
    } catch (error) {
        console.error('Failed to load lexicon:', error);
    }
}

// Load sound changes
async function loadSoundChanges() {
    if (changesContainer.style.display === 'block') {
        changesContainer.style.display = 'none';
        loadChangesBtn.textContent = 'Show Sound Changes';
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/sound_changes`);
        const data = await response.json();
        
        changesContainer.innerHTML = '';
        
        data.changes.forEach(change => {
            const card = document.createElement('div');
            card.className = 'change-card';
            card.innerHTML = `
                <h3>${change.name}</h3>
                <div class="change-rule">${change.source} → ${change.target} / ${change.environment}</div>
                <p>${change.description}</p>
                <div class="change-period">${change.period}</div>
            `;
            changesContainer.appendChild(card);
        });
        
        changesContainer.style.display = 'block';
        loadChangesBtn.textContent = 'Hide Sound Changes';
        
    } catch (error) {
        console.error('Failed to load sound changes:', error);
    }
}

// Clear input
function clearInput() {
    inputTextarea.value = '';
    resultsSection.style.display = 'none';
    resultsContainer.innerHTML = '';
}

// Allow Enter key to submit (Ctrl+Enter for newline)
inputTextarea.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.ctrlKey && !e.shiftKey) {
        e.preventDefault();
        analyzeText();
    }
});