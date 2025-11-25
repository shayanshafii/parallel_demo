// API BASE URL
const API_BASE = window.location.origin;

// UTILITY FUNCTIONS
function showMessage(message, type = 'success') {
    const messageEl = document.getElementById('message');
    if (messageEl) {
        messageEl.textContent = message;
        messageEl.className = `message ${type}`;
        messageEl.style.display = 'block';
        
        // AUTO-HIDE AFTER 5 SECONDS
        setTimeout(() => {
            messageEl.style.display = 'none';
        }, 5000);
    }
}

function hideMessage() {
    const messageEl = document.getElementById('message');
    if (messageEl) {
        messageEl.style.display = 'none';
    }
}

// SEARCH FUNCTIONALITY
const searchForm = document.getElementById('search-form');
if (searchForm) {
    searchForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        hideMessage();
        
        const objective = document.getElementById('objective').value.trim();
        const searchQueriesInput = document.getElementById('search_queries').value.trim();
        const mode = document.getElementById('mode').value;
        
        if (!objective) {
            showMessage('Please enter a search objective', 'error');
            return;
        }
        
        const searchQueries = searchQueriesInput 
            ? searchQueriesInput.split(',').map(q => q.trim()).filter(q => q)
            : null;
        
        const searchBtn = document.getElementById('search-btn');
        searchBtn.disabled = true;
        searchBtn.textContent = 'Searching...';
        
        try {
            const response = await fetch(`${API_BASE}/api/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    objective: objective,
                    search_queries: searchQueries,
                    mode: mode
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Search failed');
            }
            
            displayResults(data.results, data.search_id, objective, mode);
            showMessage(`Found ${data.results.length} result(s)`, 'success');
            
        } catch (error) {
            showMessage(`Error: ${error.message}`, 'error');
        } finally {
            searchBtn.disabled = false;
            searchBtn.textContent = 'Search';
        }
    });
}

function displayResults(results, searchId, query, mode) {
    const resultsSection = document.getElementById('results-section');
    const resultsContainer = document.getElementById('results-container');
    
    if (!results || results.length === 0) {
        resultsContainer.innerHTML = '<p class="empty-state">No results found</p>';
        resultsSection.style.display = 'block';
        return;
    }
    
    resultsContainer.innerHTML = '';
    
    results.forEach((result, index) => {
        const resultCard = document.createElement('div');
        resultCard.className = 'result-card';
        resultCard.id = `result-${index}`;
        
        const title = result.title || 'No title';
        const url = result.url;
        const publishDate = result.publish_date || 'N/A';
        const excerpts = result.excerpts || [];
        
        let excerptsHtml = '';
        if (excerpts.length > 0) {
            excerptsHtml = '<div class="result-excerpts">';
            excerpts.forEach(excerpt => {
                excerptsHtml += `<div class="excerpt">${escapeHtml(excerpt)}</div>`;
            });
            excerptsHtml += '</div>';
        }
        
        // ESCAPE HTML FOR SAFE DISPLAY
        const safeTitle = escapeHtml(title);
        const safeUrl = escapeHtml(url);
        const safePublishDate = escapeHtml(publishDate);
        const safeSearchId = escapeHtmlForAttribute(searchId);
        const safeUrlAttr = escapeHtmlForAttribute(url);
        const safeTitleAttr = escapeHtmlForAttribute(title);
        const safeQueryAttr = escapeHtmlForAttribute(query);
        const safeModeAttr = escapeHtmlForAttribute(mode);
        
        resultCard.innerHTML = `
            <div class="result-header">
                <div>
                    <div class="result-title">
                        <a href="${safeUrl}" target="_blank" rel="noopener noreferrer">${safeTitle}</a>
                    </div>
                    <div class="result-url">${safeUrl}</div>
                    <div class="result-meta">Published: ${safePublishDate}</div>
                </div>
            </div>
            ${excerptsHtml}
            <div class="feedback-buttons" data-search-id="${safeSearchId}" data-url="${safeUrlAttr}" data-title="${safeTitleAttr}" data-query="${safeQueryAttr}" data-mode="${safeModeAttr}" data-index="${index}">
                <button class="feedback-btn correct" data-correct="true">
                    ✓ Correct
                </button>
                <button class="feedback-btn incorrect" data-correct="false">
                    ✗ Incorrect
                </button>
            </div>
        `;
        
        // ADD EVENT LISTENERS TO BUTTONS
        const buttons = resultCard.querySelectorAll('.feedback-btn');
        buttons.forEach(btn => {
            btn.addEventListener('click', function() {
                const container = this.closest('.feedback-buttons');
                const isCorrect = this.dataset.correct === 'true';
                submitFeedback(
                    container.dataset.searchId,
                    container.dataset.url,
                    container.dataset.title,
                    isCorrect,
                    container.dataset.query,
                    container.dataset.mode,
                    parseInt(container.dataset.index)
                );
            });
        });
        
        resultsContainer.appendChild(resultCard);
    });
    
    resultsSection.style.display = 'block';
}

async function submitFeedback(searchId, resultUrl, resultTitle, isCorrect, query, mode, resultIndex) {
    const resultCard = document.getElementById(`result-${resultIndex}`);
    const feedbackButtons = resultCard.querySelector('.feedback-buttons');
    
    // DISABLE ALL BUTTONS
    feedbackButtons.querySelectorAll('button').forEach(btn => {
        btn.disabled = true;
    });
    
    try {
        const response = await fetch(`${API_BASE}/api/evaluate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                search_id: searchId,
                result_url: resultUrl,
                result_title: resultTitle,
                is_correct: isCorrect,
                query: query,
                mode: mode
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to save evaluation');
        }
        
        // SHOW SUCCESS STATUS
        const statusClass = isCorrect ? 'correct' : 'incorrect';
        const statusText = isCorrect ? 'Marked as Correct' : 'Marked as Incorrect';
        feedbackButtons.innerHTML = `
            <span class="feedback-status ${statusClass}">${statusText}</span>
        `;
        
        showMessage('Feedback saved successfully', 'success');
        
    } catch (error) {
        showMessage(`Error: ${error.message}`, 'error');
        // RE-ENABLE BUTTONS ON ERROR
        feedbackButtons.querySelectorAll('button').forEach(btn => {
            btn.disabled = false;
        });
    }
}

// EVALUATIONS PAGE FUNCTIONALITY
async function loadEvaluations() {
    const container = document.getElementById('evaluations-container');
    const statsContainer = document.getElementById('statistics-container');
    if (!container) return;
    
    container.innerHTML = '<p class="loading">Loading evaluations...</p>';
    if (statsContainer) {
        statsContainer.innerHTML = '<p class="loading">Loading statistics...</p>';
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/evaluations`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to load evaluations');
        }
        
        // DISPLAY STATISTICS
        if (statsContainer && data.statistics) {
            const stats = data.statistics;
            statsContainer.innerHTML = `
                <div class="statistics-grid">
                    <div class="stat-item">
                        <div class="stat-mode">Agentic</div>
                        <div class="stat-values">
                            <span>Correct: ${stats.agentic.correct}</span>
                            <span>Incorrect: ${stats.agentic.incorrect}</span>
                        </div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-mode">One-Shot</div>
                        <div class="stat-values">
                            <span>Correct: ${stats['one-shot'].correct}</span>
                            <span>Incorrect: ${stats['one-shot'].incorrect}</span>
                        </div>
                    </div>
                </div>
            `;
        }
        
        const evaluations = data.evaluations || [];
        
        if (evaluations.length === 0) {
            container.innerHTML = '<p class="empty-state">No evaluations found</p>';
            return;
        }
        
        container.innerHTML = '';
        
        evaluations.forEach(eval => {
            const evalItem = document.createElement('div');
            evalItem.className = 'evaluation-item';
            
            const date = new Date(eval.created_at);
            const dateStr = date.toLocaleString();
            const statusClass = eval.is_correct ? 'correct' : 'incorrect';
            const statusText = eval.is_correct ? 'Correct' : 'Incorrect';
            
            evalItem.innerHTML = `
                <div class="evaluation-header">
                    <div>
                        <div class="evaluation-query">${escapeHtml(eval.query)}</div>
                        <div class="evaluation-meta">
                            Mode: ${eval.mode} | 
                            Search ID: ${eval.search_id} | 
                            <span class="feedback-status ${statusClass}">${statusText}</span>
                        </div>
                    </div>
                    <div class="evaluation-meta">${dateStr}</div>
                </div>
                <div class="evaluation-result">
                    <a href="${escapeHtml(eval.result_url)}" target="_blank" rel="noopener noreferrer" class="evaluation-result-url">
                        ${escapeHtml(eval.result_title || eval.result_url)}
                    </a>
                </div>
            `;
            
            container.appendChild(evalItem);
        });
        
    } catch (error) {
        container.innerHTML = `<p class="empty-state error">Error loading evaluations: ${error.message}</p>`;
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ESCAPE HTML FUNCTION FOR USE IN DISPLAYRESULTS
function escapeHtmlForAttribute(text) {
    if (!text) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#x27;');
}

