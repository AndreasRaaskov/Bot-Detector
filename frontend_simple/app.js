// Bot Detector - Main Application JavaScript

// Configuration
// If running on port 8080 (dev server), API is on 8000
// If running on port 8000 (production), API is on same origin
const API_BASE_URL = window.location.port === '8080'
    ? 'http://localhost:8000'
    : window.location.origin;
const API_ENDPOINT = `${API_BASE_URL}/analyze`;

// State management
const state = {
    analyzedHandle: null,
    results: {
        followRatio: null,
        postingPattern: null,
        textAnalysis: null,
        llmDetection: null,
        overallScore: null
    }
};

// DOM Elements
const elements = {
    form: document.getElementById('analyzeForm'),
    handleInput: document.getElementById('handleInput'),
    toast: document.getElementById('toast'),
    loading: document.getElementById('loading'),
    analyzedHandle: document.getElementById('analyzedHandle'),
    handleName: document.getElementById('handleName'),

    // Score elements
    followRatioScore: document.getElementById('followRatioScore'),
    followRatioProgress: document.getElementById('followRatioProgress'),
    postingPatternScore: document.getElementById('postingPatternScore'),
    postingPatternProgress: document.getElementById('postingPatternProgress'),
    textAnalysisScore: document.getElementById('textAnalysisScore'),
    textAnalysisProgress: document.getElementById('textAnalysisProgress'),
    llmDetectionScore: document.getElementById('llmDetectionScore'),
    llmDetectionProgress: document.getElementById('llmDetectionProgress'),
    overallScore: document.getElementById('overallScore'),
    overallProgress: document.getElementById('overallProgress')
};

// Toast notification function
function showToast(title, description, isError = false) {
    const toast = elements.toast;

    toast.innerHTML = `
        <div class="toast-title">${title}</div>
        <div class="toast-description">${description}</div>
    `;

    toast.classList.toggle('error', isError);
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Determine score color class based on value
function getScoreClass(score) {
    if (score === null) return 'score-neutral';
    if (score < 30) return 'score-low';
    if (score < 70) return 'score-medium';
    return 'score-high';
}

// Format score for display
function formatScore(score) {
    return score === null ? 'NaN' : `${score.toFixed(1)}%`;
}

// Update a single score display
function updateScore(scoreElement, progressElement, value) {
    const score = value !== null ? value : null;

    // Update score text
    scoreElement.textContent = formatScore(score);

    // Update score color
    scoreElement.className = `score-value ${getScoreClass(score)}`;

    // Update progress bar
    if (score !== null) {
        progressElement.style.width = `${score}%`;

        // Color the progress bar based on score
        if (score < 30) {
            progressElement.style.backgroundColor = 'hsl(142, 72%, 29%)';
        } else if (score < 70) {
            progressElement.style.backgroundColor = 'hsl(38, 92%, 50%)';
        } else {
            progressElement.style.backgroundColor = 'hsl(0, 72%, 51%)';
        }
    } else {
        progressElement.style.width = '0%';
        progressElement.style.backgroundColor = 'hsl(200, 98%, 39%)';
    }
}

// Update all results on the page
function updateResults(results) {
    // Update individual scores
    updateScore(
        elements.followRatioScore,
        elements.followRatioProgress,
        results.followRatio
    );

    updateScore(
        elements.postingPatternScore,
        elements.postingPatternProgress,
        results.postingPattern
    );

    updateScore(
        elements.textAnalysisScore,
        elements.textAnalysisProgress,
        results.textAnalysis
    );

    updateScore(
        elements.llmDetectionScore,
        elements.llmDetectionProgress,
        results.llmDetection
    );

    updateScore(
        elements.overallScore,
        elements.overallProgress,
        results.overallScore
    );
}

// Analyze a Bluesky handle
async function analyzeHandle(handle) {
    try {
        // Show loading indicator
        elements.loading.style.display = 'block';

        // Make API request
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                bluesky_handle: handle
            })
        });

        // Hide loading indicator
        elements.loading.style.display = 'none';

        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }

        const data = await response.json();
        console.log('API Response:', data);

        // Update state with results (convert 0-1 scale to 0-100 percentage)
        state.results = {
            followRatio: data.follow_analysis?.score !== undefined
                ? data.follow_analysis.score * 100
                : null,
            postingPattern: data.posting_pattern?.score !== undefined
                ? data.posting_pattern.score * 100
                : null,
            textAnalysis: data.text_analysis?.score !== undefined
                ? data.text_analysis.score * 100
                : null,
            llmDetection: data.llm_analysis?.score !== undefined
                ? data.llm_analysis.score * 100
                : null,
            overallScore: data.overall_score !== undefined
                ? data.overall_score * 100
                : null
        };

        // Update UI
        state.analyzedHandle = handle;
        elements.handleName.textContent = `@${handle}`;
        elements.analyzedHandle.style.display = 'block';
        updateResults(state.results);

        // Show success toast
        showToast('Analysis complete', `Results for @${handle} are ready`);

    } catch (error) {
        console.error('Analysis failed:', error);
        elements.loading.style.display = 'none';
        showToast('Analysis failed', error.message, true);
    }
}

// Handle form submission
function handleFormSubmit(event) {
    event.preventDefault();

    const handle = elements.handleInput.value.trim();

    if (!handle) {
        showToast('Handle required', 'Please enter a Bluesky handle', true);
        return;
    }

    // Clean handle (remove @ if present)
    const cleanHandle = handle.replace(/^@/, '');

    // Show starting toast
    showToast('Analysis started', `Analyzing @${cleanHandle}...`);

    // Start analysis
    analyzeHandle(cleanHandle);
}

// Initialize the application
function init() {
    // Set up form submission handler
    elements.form.addEventListener('submit', handleFormSubmit);

    console.log('Bot Detector initialized');
}

// Run initialization when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
