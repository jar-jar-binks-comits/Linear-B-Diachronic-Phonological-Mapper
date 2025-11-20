// API Configuration
const API_BASE = 'http://localhost:5000/api';

// DOM Elements
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

// Paradigm elements
const paradigmSection = document.getElementById('paradigm-section');
const paradigmWord = document.getElementById('paradigm-word');
const generateParadigmBtn = document.getElementById('generate-paradigm-btn');
const paradigmResults = document.getElementById('paradigm-results');

// Global mapper instance
let diachronicMapper = null;

// Event Listeners
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

if (generateParadigmBtn) {
    generateParadigmBtn.addEventListener('click', generateParadigm);
}

inputTextarea.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.ctrlKey && !e.shiftKey) {
        e.preventDefault();
        analyzeText();
    }
});

// Main Analysis Function
async function analyzeText() {
    const text = inputTextarea.value.trim();
    
    if (!text) {
        alert('Please enter Linear B text');
        return;
    }
    
    analyzeBtn.classList.add('loading');
    analyzeBtn.textContent = 'Analyzing...';
    
    try {
        const response = await fetch(`${API_BASE}/full_analysis`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        
        if (!response.ok) throw new Error('Analysis failed');
        
        const data = await response.json();
        displayResults(data.results);
        
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
    }
}

// Display Results with Side-by-Side Layout
function displayResults(results) {
    resultsContainer.innerHTML = '';
    resultsSection.style.display = 'block';
    
    if (!results || results.length === 0) {
        resultsContainer.innerHTML = '<p style="text-align:center;padding:2rem;">No results found.</p>';
        return;
    }
    
    results.forEach((word, index) => {
        const resultWrapper = document.createElement('div');
        resultWrapper.className = 'result-wrapper';
        
        // LEFT COLUMN: Linguistic Analysis
        const analysisColumn = document.createElement('div');
        analysisColumn.className = 'analysis-column';
        
        // Word Header
        let html = `
            <div class="word-header">
                <span class="linear-b-text">${word.original}</span>
                <div class="transliteration-group">
                    <span class="transliteration">${word.transliteration}</span>
                    <span class="phonetic">/${word.phonetic}/</span>
                </div>
            </div>
        `;
        
        html += '<div class="analysis-grid">';
        
        // Morphology Card
        if (word.morphology) {
            html += `
                <div class="analysis-card morphology-card">
                    <h4>📐 Morphological Analysis</h4>
                    <div class="card-content">
                        <div class="info-row">
                            <span class="label">Stem:</span>
                            <span class="value">${word.morphology.stem}</span>
                        </div>
                        <div class="info-row">
                            <span class="label">Ending:</span>
                            <span class="value">-${word.morphology.ending || '∅'}</span>
                        </div>
                        ${word.morphology.case ? `
                        <div class="info-row">
                            <span class="label">Case:</span>
                            <span class="value">${word.morphology.case}</span>
                        </div>` : ''}
                        ${word.morphology.number ? `
                        <div class="info-row">
                            <span class="label">Number:</span>
                            <span class="value">${word.morphology.number}</span>
                        </div>` : ''}
                        ${word.morphology.declension ? `
                        <div class="info-row">
                            <span class="label">Declension:</span>
                            <span class="value">${word.morphology.declension.replace(/_/g, ' ')}</span>
                        </div>` : ''}
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: ${word.morphology.confidence * 100}%"></div>
                            <span class="confidence-text">${(word.morphology.confidence * 100).toFixed(0)}% confidence</span>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // Classical Greek Card
        if (word.diachronic) {
            html += `
                <div class="analysis-card classical-card">
                    <h4>🏛️ Classical Greek</h4>
                    <div class="card-content">
                        <div class="classical-form">${word.diachronic.classical}</div>
                        <div class="meaning">"${word.diachronic.meaning}"</div>
                        <div class="changes-count">
                            ${word.diachronic.total_changes} phonological change${word.diachronic.total_changes !== 1 ? 's' : ''} applied
                        </div>
                    </div>
                </div>
            `;
            
            // PIE Etymology Card
            if (word.diachronic.pie_root) {
                html += `
                    <div class="analysis-card pie-card">
                        <h4>🌳 Proto-Indo-European</h4>
                        <div class="card-content">
                            <div class="pie-root">${word.diachronic.pie_root}</div>
                            ${word.diachronic.pie_meaning ? `<div class="pie-meaning">"${word.diachronic.pie_meaning}"</div>` : ''}
                            ${word.diachronic.cognates ? `
                            <div class="cognates">
                                <strong>Cognates:</strong>
                                ${Object.entries(word.diachronic.cognates).map(([lang, form]) => 
                                    `<span class="cognate"><em>${lang}:</em> ${form}</span>`
                                ).join('')}
                            </div>` : ''}
                        </div>
                    </div>
                `;
            }
        }
        
        html += '</div>';
        analysisColumn.innerHTML = html;
        
        // RIGHT COLUMN: Diachronic Visualization
        const visualColumn = document.createElement('div');
        visualColumn.className = 'visual-column';
        visualColumn.innerHTML = `
            <div class="mapper-container">
                <h4>⏳ Diachronic Evolution</h4>
                <div id="mapper-${index}" class="mapper-canvas"></div>
            </div>
        `;
        
        resultWrapper.appendChild(analysisColumn);
        resultWrapper.appendChild(visualColumn);
        resultsContainer.appendChild(resultWrapper);
        
        // Render diachronic visualization
        if (word.diachronic && word.diachronic.stages) {
            setTimeout(() => {
                renderDiachronicPath(
                    `mapper-${index}`,
                    word.transliteration.replace(/-/g, ''),
                    word.diachronic.classical
                );
            }, 100);
        }
    });
    
    // Show paradigm section and populate
    showParadigmSection();
    if (results.length > 0 && paradigmWord) {
        paradigmWord.value = results[0].transliteration;
    }
}

// Render Diachronic Visualization
async function renderDiachronicPath(containerId, mycenaean, classical) {
    try {
        const response = await fetch(`${API_BASE}/diachronic`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mycenaean, classical })
        });
        
        if (!response.ok) throw new Error('Diachronic fetch failed');
        
        const data = await response.json();
        
        const mapper = new DiachronicMapper(containerId, {
            width: 420,
            height: 550,
            layout: 'vertical'
        });
        
        mapper.visualize(data);
        
    } catch (error) {
        console.error('Mapper error:', error);
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div style="padding: 2rem; text-align: center; color: var(--base01);">
                    <p>Visualization unavailable</p>
                </div>
            `;
        }
    }
}

// Paradigm Generator Functions
function showParadigmSection() {
    if (paradigmSection) {
        paradigmSection.style.display = 'block';
    }
}

async function generateParadigm() {
    const word = paradigmWord.value.trim();
    
    if (!word) {
        alert('Enter a word transliteration');
        return;
    }
    
    generateParadigmBtn.textContent = 'Generating...';
    generateParadigmBtn.disabled = true;
    
    try {
        // Try from lexicon first
        let response = await fetch(`${API_BASE}/generate/${word}`);
        
        if (!response.ok) {
            // Manual generation fallback
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
        displayParadigm(data);
        
    } catch (error) {
        console.error('Paradigm generation error:', error);
        alert('Failed to generate paradigm');
    } finally {
        generateParadigmBtn.textContent = 'Generate Paradigm';
        generateParadigmBtn.disabled = false;
    }
}

function displayParadigm(data) {
    paradigmResults.style.display = 'block';
    
    const statsContainer = paradigmResults.querySelector('.paradigm-stats');
    const tableContainer = paradigmResults.querySelector('.paradigm-table-container');
    
    // Stats
    statsContainer.innerHTML = `
        <div class="paradigm-stats-grid">
            <div class="stat-card">
                <div class="stat-value">${data.total_forms || data.total}</div>
                <div class="stat-label">Total Forms</div>
            </div>
            <div class="stat-card attested">
                <div class="stat-value">${data.attested || 0}</div>
                <div class="stat-label">Attested on Tablets</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${data.coverage || '0%'}</div>
                <div class="stat-label">Coverage</div>
            </div>
        </div>
    `;
    
    // Lemma info if available
    if (data.lemma_data) {
        let lemmaHTML = '<div class="lemma-info">';
        if (data.lemma_data.meaning) {
            lemmaHTML += `<p><strong>Meaning:</strong> ${data.lemma_data.meaning}</p>`;
        }
        if (data.lemma_data.classical) {
            lemmaHTML += `<p><strong>Classical:</strong> ${data.lemma_data.classical}</p>`;
        }
        if (data.lemma_data.pie_root) {
            lemmaHTML += `<p><strong>PIE Root:</strong> ${data.lemma_data.pie_root}`;
            if (data.lemma_data.pie_meaning) {
                lemmaHTML += ` "${data.lemma_data.pie_meaning}"`;
            }
            lemmaHTML += `</p>`;
        }
        lemmaHTML += '</div>';
        statsContainer.innerHTML += lemmaHTML;
    }
    
    // Paradigm table
    const forms = data.generated_paradigm || data.forms;
    
    // Group by case
    const byCase = {};
    forms.forEach(form => {
        const caseKey = form.case || 'other';
        if (!byCase[caseKey]) byCase[caseKey] = [];
        byCase[caseKey].push(form);
    });
    
    let tableHTML = '<div class="paradigm-table">';
    
    Object.entries(byCase).forEach(([caseName, caseForms]) => {
        tableHTML += `
            <div class="case-group">
                <h4 class="case-header">${caseName.toUpperCase()}</h4>
                <div class="forms-grid">
        `;
        
        caseForms.forEach(form => {
            const attestedClass = form.attested ? 'attested' : 'theoretical';
            const badge = form.attested 
                ? '<span class="badge-attested">✓ Attested</span>' 
                : '<span class="badge-theoretical">Theoretical</span>';
            
            tableHTML += `
                <div class="form-card ${attestedClass}">
                    <div class="form-transliteration">${form.form}</div>
                    <div class="form-details">
                        <span class="form-number">${form.number || ''}</span>
                        ${badge}
                    </div>
                    <div class="form-reconstruction">*${form.reconstruction}</div>
                </div>
            `;
        });
        
        tableHTML += '</div></div>';
    });
    
    tableHTML += '</div>';
    tableContainer.innerHTML = tableHTML;
    
    paradigmResults.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Load Lexicon
async function loadLexicon() {
    if (lexiconContainer.style.display === 'block') {
        lexiconContainer.style.display = 'none';
        loadLexiconBtn.textContent = 'Load Full Lexicon';
        return;
    }
    
    loadLexiconBtn.textContent = 'Loading...';
    
    try {
        const response = await fetch(`${API_BASE}/lexicon`);
        const data = await response.json();
        
        lexiconContainer.innerHTML = '<div class="lexicon-grid"></div>';
        const grid = lexiconContainer.querySelector('.lexicon-grid');
        
        const sortedWords = data.words.sort((a, b) => 
            (a.meaning || '').localeCompare(b.meaning || '')
        );
        
        sortedWords.forEach(word => {
            const item = document.createElement('div');
            item.className = 'lexicon-item';
            item.innerHTML = `
                <div class="lex-trans">${word.transliteration}</div>
                <div class="lex-meaning">${word.meaning}</div>
                <div class="lex-classical">${word.classical}</div>
                ${word.pie_root ? `<div class="lex-pie">${word.pie_root}</div>` : ''}
            `;
            item.addEventListener('click', () => {
                inputTextarea.value = word.transliteration;
                inputTextarea.scrollIntoView({ behavior: 'smooth' });
            });
            grid.appendChild(item);
        });
        
        lexiconContainer.style.display = 'block';
        loadLexiconBtn.textContent = `Hide Lexicon (${data.words.length} words)`;
        
    } catch (error) {
        console.error('Failed to load lexicon:', error);
        loadLexiconBtn.textContent = 'Load Full Lexicon';
    }
}

// Load Sound Changes
async function loadSoundChanges() {
    if (changesContainer.style.display === 'block') {
        changesContainer.style.display = 'none';
        loadChangesBtn.textContent = 'Show Sound Changes';
        return;
    }
    
    loadChangesBtn.textContent = 'Loading...';
    
    try {
        const response = await fetch(`${API_BASE}/sound_changes`);
        const data = await response.json();
        
        changesContainer.innerHTML = '';
        
        data.changes.forEach((change, index) => {
            const card = document.createElement('div');
            card.className = 'change-card';
            card.innerHTML = `
                <div class="change-header">
                    <span class="change-number">${index + 1}</span>
                    <h3>${change.name}</h3>
                </div>
                <div class="change-rule">${change.source} → ${change.target} / ${change.environment}</div>
                <p class="change-desc">${change.description}</p>
                <div class="change-period">📅 ${change.period}</div>
                ${change.examples && change.examples.length > 0 ? `
                <div class="change-examples">
                    <strong>Examples:</strong>
                    ${change.examples.slice(0, 3).map(ex => 
                        `<span class="example">${ex[0]} → ${ex[1]}</span>`
                    ).join('')}
                </div>
                ` : ''}
            `;
            changesContainer.appendChild(card);
        });
        
        changesContainer.style.display = 'block';
        loadChangesBtn.textContent = `Hide Sound Changes (${data.changes.length} rules)`;
        
    } catch (error) {
        console.error('Failed to load sound changes:', error);
        loadChangesBtn.textContent = 'Show Sound Changes';
    }
}
// Clear Input
function clearInput() {
    inputTextarea.value = '';
    resultsSection.style.display = 'none';
    resultsContainer.innerHTML = '';
    if (paradigmSection) {
        paradigmSection.style.display = 'none';
    }
    if (paradigmResults) {
        paradigmResults.style.display = 'none';
    }
}

// Load syllabary on page load
async function loadSyllabary() {
    try {
        const response = await fetch(`${API_BASE.replace('/api', '')}/data/syllabary.json`);
        const data = await response.json();
        const grid = document.getElementById('syllabary-grid');
        
        if (!grid) return;
        
        // Sort by transliteration for easier finding
        const sortedSigns = Object.entries(data.signs).sort((a, b) => 
            a[1].transliteration.localeCompare(b[1].transliteration)
        );
        
        sortedSigns.forEach(([unicode, info]) => {
            const btn = document.createElement('button');
            btn.className = 'syllabary-sign';
            btn.innerHTML = `
                <span class="sign">${unicode}</span>
                <span class="label">${info.transliteration}</span>
            `;
            btn.title = `${info.transliteration} - Click to insert`;
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

// Initialise on page load
document.addEventListener('DOMContentLoaded', () => {
    loadSyllabary();
    console.log('Linear B Diachronic Phonological Mapper initialized');
    console.log('API endpoint:', API_BASE);
});