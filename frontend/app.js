// API Configuration
const API_BASE_URL = 'http://127.0.0.1:8000';

// DOM Elements
const goalForm = document.getElementById('goalForm');
const goalInput = document.getElementById('goalInput');
const submitBtn = document.getElementById('submitBtn');
const progressSection = document.getElementById('progressSection');
const resultsSection = document.getElementById('resultsSection');
const stepsList = document.getElementById('stepsList');
const resultsList = document.getElementById('resultsList');
const historyList = document.getElementById('historyList');
const refreshHistoryBtn = document.getElementById('refreshHistoryBtn');

// State
let currentExecution = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
    refreshHistoryBtn.addEventListener('click', loadHistory);
    
    // Close results button
    const closeResultsBtn = document.getElementById('closeResultsBtn');
    closeResultsBtn.addEventListener('click', () => {
        resultsSection.style.display = 'none';
    });
    
    // Match heights of input and history sections
    matchSectionHeights();
    window.addEventListener('resize', matchSectionHeights);
    
    // Also match heights after a short delay to ensure DOM is ready
    setTimeout(matchSectionHeights, 100);
});

// Match heights of input and history sections
function matchSectionHeights() {
    const inputCard = document.querySelector('.input-section .card');
    const historyCard = document.querySelector('.history-section .card');
    
    if (inputCard && historyCard) {
        // Reset heights to get natural measurements
        inputCard.style.height = 'auto';
        historyCard.style.height = 'auto';
        
        // Force reflow to get accurate measurements
        void inputCard.offsetHeight;
        void historyCard.offsetHeight;
        
        // Get the natural height of the input card
        const inputHeight = inputCard.offsetHeight;
        
        // Always set history card to match input card height
        historyCard.style.height = `${inputHeight}px`;
        historyCard.style.minHeight = `${inputHeight}px`;
        historyCard.style.maxHeight = `${inputHeight}px`;
    }
}

// Form Submission
goalForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const goal = goalInput.value.trim();
    
    if (!goal) return;
    
    // Reset UI
    resetUI();
    showProgress();
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="btn-icon">⏳</span> Processing...';
    
    try {
        const response = await fetch(`${API_BASE_URL}/run?goal=${encodeURIComponent(goal)}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayResults(data);
        loadHistory(); // Refresh history
        
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to execute goal. Please check if the server is running.');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span class="btn-icon">🚀</span> Start Agent';
        goalInput.value = '';
    }
});

// Reset UI
function resetUI() {
    progressSection.style.display = 'none';
    resultsSection.style.display = 'none';
    stepsList.innerHTML = '';
    resultsList.innerHTML = '';
}

// Show Progress
function showProgress() {
    progressSection.style.display = 'block';
    updateProgress(0, 0, 'Initializing...');
}

// Update Progress
function updateProgress(current, total, complexity = '-') {
    document.getElementById('complexityValue').textContent = complexity;
    document.getElementById('stepsValue').textContent = `${current}/${total}`;
    
    const progressFill = document.getElementById('progressFill');
    const percentage = total > 0 ? (current / total) * 100 : 0;
    progressFill.style.width = `${percentage}%`;
}

// Display Results
function displayResults(data) {
    progressSection.style.display = 'none';
    resultsSection.style.display = 'block';
    
    // Update execution time
    const timeFormatted = data.execution_time?.formatted || 'N/A';
    document.getElementById('executionTime').textContent = timeFormatted;
    
    // Update API statistics
    const stats = data.api_statistics || {};
    document.getElementById('planningCalls').textContent = stats.planning !== undefined ? stats.planning : '-';
    document.getElementById('executionCalls').textContent = stats.execution !== undefined ? stats.execution : '-';
    document.getElementById('evaluationCalls').textContent = stats.evaluation !== undefined ? stats.evaluation : '-';
    document.getElementById('correctionCalls').textContent = stats.self_correction !== undefined ? stats.self_correction : '-';
    document.getElementById('totalApiCalls').textContent = stats.total !== undefined ? stats.total : '-';
    
    // Display combined results
    resultsList.innerHTML = '';
    if (data.results && data.results.length > 0) {
        // Combine all outputs into one block
        const combinedOutput = data.results.map(r => r.output).join('\n\n');
        const resultItem = createCombinedResultItem(combinedOutput);
        resultsList.appendChild(resultItem);
    } else {
        resultsList.innerHTML = '<div class="empty-state">No results available</div>';
    }
}

// Create Combined Result Item (all outputs in one block)
function createCombinedResultItem(combinedOutput) {
    const item = document.createElement('div');
    item.className = 'result-item';
    
    // Render markdown to HTML
    const renderedContent = renderMarkdown(combinedOutput);
    
    // Create wrapper
    const wrapper = document.createElement('div');
    wrapper.className = 'result-output-wrapper';
    
    // Create top copy button
    const copyBtnTop = document.createElement('button');
    copyBtnTop.className = 'copy-btn copy-btn-top';
    copyBtnTop.innerHTML = '<span class="copy-icon">📋</span> Copy Output';
    copyBtnTop.onclick = () => copyToClipboard(combinedOutput, copyBtnTop);
    
    // Create output div
    const outputDiv = document.createElement('div');
    outputDiv.className = 'result-output markdown-content';
    outputDiv.innerHTML = renderedContent;
    
    // Create bottom copy button
    const copyBtnBottom = document.createElement('button');
    copyBtnBottom.className = 'copy-btn copy-btn-bottom';
    copyBtnBottom.innerHTML = '<span class="copy-icon">📋</span> Copy Output';
    copyBtnBottom.onclick = () => copyToClipboard(combinedOutput, copyBtnBottom);
    
    wrapper.appendChild(copyBtnTop);
    wrapper.appendChild(outputDiv);
    wrapper.appendChild(copyBtnBottom);
    item.appendChild(wrapper);
    
    return item;
}

// Copy to clipboard function
function copyToClipboard(text, button) {
    navigator.clipboard.writeText(text).then(() => {
        const originalHTML = button.innerHTML;
        button.innerHTML = '<span class="copy-icon">✅</span> Copied!';
        button.style.background = 'var(--success)';
        setTimeout(() => {
            button.innerHTML = originalHTML;
            button.style.background = '';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
        const originalHTML = button.innerHTML;
        button.innerHTML = '<span class="copy-icon">❌</span> Failed';
        setTimeout(() => {
            button.innerHTML = '<span class="copy-icon">📋</span> Copy Output';
        }, 2000);
    });
}

// Simple Markdown Renderer
function renderMarkdown(text) {
    if (!text) return '';
    
    let html = escapeHtml(text);
    
    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
    
    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/__(.*?)__/g, '<strong>$1</strong>');
    
    // Italic
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    html = html.replace(/_(.*?)_/g, '<em>$1</em>');
    
    // Code blocks
    html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
    
    // Lists
    html = html.replace(/^\* (.*$)/gim, '<li>$1</li>');
    html = html.replace(/^- (.*$)/gim, '<li>$1</li>');
    html = html.replace(/^(\d+)\. (.*$)/gim, '<li>$2</li>');
    
    // Wrap consecutive list items in ul
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
    
    // Horizontal rules
    html = html.replace(/^---$/gim, '<hr>');
    html = html.replace(/^\*\*\*$/gim, '<hr>');
    
    // Tables (improved support - skip separator rows)
    const lines = html.split('\n');
    let inTable = false;
    let tableRows = [];
    let processedLines = [];
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        // Check if it's a table row (has |) and not a separator row
        if (line.includes('|') && !line.match(/^[\|\s\-:]+$/)) {
            if (!inTable) {
                inTable = true;
                tableRows = [];
            }
            const cells = line.split('|').map(cell => cell.trim()).filter(cell => cell);
            // Skip separator rows (rows with only dashes and colons)
            const isSeparator = cells.every(cell => cell.match(/^:?-+:?$/) || cell === '');
            if (cells.length > 0 && !isSeparator) {
                tableRows.push(cells);
            }
        } else {
            // Check if next line is separator - skip it
            if (i + 1 < lines.length && lines[i + 1].trim().match(/^[\|\s\-:]+$/)) {
                i++; // Skip the separator line
                continue;
            }
            
            if (inTable && tableRows.length > 0) {
                // Process table
                let tableHtml = '<table>';
                tableRows.forEach((row, idx) => {
                    if (idx === 0) {
                        // Header row
                        tableHtml += '<thead><tr>' + row.map(cell => `<th>${cell}</th>`).join('') + '</tr></thead><tbody>';
                    } else {
                        tableHtml += '<tr>' + row.map(cell => `<td>${cell}</td>`).join('') + '</tr>';
                    }
                });
                if (tableRows.length > 1) {
                    tableHtml += '</tbody>';
                } else {
                    tableHtml += '<tbody></tbody>';
                }
                tableHtml += '</table>';
                processedLines.push(tableHtml);
                tableRows = [];
                inTable = false;
            }
            if (line && !line.match(/^[\|\s\-:]+$/)) {
                processedLines.push(line);
            }
        }
    }
    
    // Handle table at end
    if (inTable && tableRows.length > 0) {
        let tableHtml = '<table>';
        tableRows.forEach((row, idx) => {
            if (idx === 0) {
                tableHtml += '<thead><tr>' + row.map(cell => `<th>${cell}</th>`).join('') + '</tr></thead><tbody>';
            } else {
                tableHtml += '<tr>' + row.map(cell => `<td>${cell}</td>`).join('') + '</tr>';
            }
        });
        if (tableRows.length > 1) {
            tableHtml += '</tbody>';
        } else {
            tableHtml += '<tbody></tbody>';
        }
        tableHtml += '</table>';
        processedLines.push(tableHtml);
    }
    
    html = processedLines.join('\n');
    
    // Clean up extra spacing
    html = html.replace(/\n{3,}/g, '\n\n'); // Max 2 consecutive newlines
    
    // Paragraphs (convert double newlines to paragraphs, but preserve spacing)
    const blocks = html.split(/\n\n+/);
    html = blocks.map(block => {
        block = block.trim();
        if (!block) return '';
        // Don't wrap if already a block element
        if (block.match(/^<(h[1-6]|ul|ol|pre|table|hr|p)/)) return block;
        // Convert single newlines within paragraphs to <br>
        block = block.replace(/\n/g, '<br>');
        return '<p>' + block + '</p>';
    }).filter(b => b).join('');
    
    return html;
}

// Load History
async function loadHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/goals`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayHistory(data);
        
    } catch (error) {
        console.error('Error loading history:', error);
        historyList.innerHTML = '<div class="empty-state">Failed to load history</div>';
    }
}

// Display History
function displayHistory(data) {
    historyList.innerHTML = '';
    
    if (!data.goals || data.goals.length === 0) {
        historyList.innerHTML = '<div class="empty-state">No previous results</div>';
        matchSectionHeights();
        return;
    }
    
    // Display all goals
    data.goals.forEach((goalData) => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        
        // Get execution time - handle both formats
        let timeFormatted = 'N/A';
        if (goalData.execution_time) {
            timeFormatted = goalData.execution_time.duration_formatted || 
                          goalData.execution_time.formatted || 
                          (goalData.execution_time.duration_seconds ? 
                            formatDuration(goalData.execution_time.duration_seconds) : 'N/A');
        }
        
        historyItem.innerHTML = `
            <div class="history-content">
                <div class="history-goal">${escapeHtml(goalData.goal)}</div>
                <div class="history-meta">
                    <span>⏱️ ${timeFormatted}</span>
                    <span>📊 ${goalData.step_count} steps</span>
                </div>
            </div>
        `;
        
        historyItem.addEventListener('click', async () => {
            // Fetch full results for this goal
            try {
                const response = await fetch(`${API_BASE_URL}/results?goal=${encodeURIComponent(goalData.goal)}`);
                if (response.ok) {
                    const resultData = await response.json();
                    displayHistoryResults(resultData);
                }
            } catch (error) {
                console.error('Error loading goal results:', error);
            }
        });
        
        historyList.appendChild(historyItem);
    });
    
    // Match heights after history is loaded
    setTimeout(matchSectionHeights, 50);
}

// Format duration helper
function formatDuration(seconds) {
    if (seconds < 60) {
        return `${seconds.toFixed(1)} seconds`;
    } else if (seconds < 3600) {
        return `${(seconds / 60).toFixed(1)} minutes`;
    } else {
        return `${(seconds / 3600).toFixed(2)} hours`;
    }
}

// Display History Results
function displayHistoryResults(data) {
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth' });
    
    // Update execution time (use stored time, not recalculated)
    if (data.execution_time) {
        const timeFormatted = data.execution_time.duration_formatted || data.execution_time.formatted || 'N/A';
        document.getElementById('executionTime').textContent = timeFormatted;
    } else {
        document.getElementById('executionTime').textContent = 'N/A';
    }
    
    // Update API stats from stored data
    const stats = data.api_statistics || {};
    document.getElementById('planningCalls').textContent = stats.planning !== undefined ? stats.planning : '-';
    document.getElementById('executionCalls').textContent = stats.execution !== undefined ? stats.execution : '-';
    document.getElementById('evaluationCalls').textContent = stats.evaluation !== undefined ? stats.evaluation : '-';
    document.getElementById('correctionCalls').textContent = stats.self_correction !== undefined ? stats.self_correction : '-';
    document.getElementById('totalApiCalls').textContent = stats.total !== undefined ? stats.total : '-';
    
    // Display combined results
    resultsList.innerHTML = '';
    if (data.results && data.results.length > 0) {
        // Combine all outputs into one block
        const combinedOutput = data.results.map(r => r.output).join('\n\n');
        const resultItem = createCombinedResultItem(combinedOutput);
        resultsList.appendChild(resultItem);
    }
}

// Show Error
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'card';
    errorDiv.style.border = `2px solid var(--error)`;
    errorDiv.style.background = 'rgba(239, 68, 68, 0.1)';
    errorDiv.innerHTML = `
        <h3 style="color: var(--error); margin-bottom: 0.5rem;">Error</h3>
        <p style="color: var(--text-primary);">${escapeHtml(message)}</p>
    `;
    
    resultsSection.style.display = 'block';
    resultsList.innerHTML = '';
    resultsList.appendChild(errorDiv);
}

// Utility: Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Simulate real-time progress (if needed)
// This would require WebSocket or polling for real-time updates
// For now, we just show the final results

