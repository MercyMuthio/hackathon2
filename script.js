// ==================== GLOBAL CONFIG ====================
const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_BASE = isLocal ? 'http://localhost:5000' : 'https://your-heroku-app.herokuapp.com';

// ==================== DEMO FUNCTIONS ====================
function showDemoMessage(containerId, message) {
    const container = document.getElementById(containerId);
    container.innerHTML = `
        <div class="demo-message">
            <h3>Demo Mode 🎭</h3>
            <p>${message}</p>
            <p class="success">This is a demonstration. Actual functionality requires backend deployment.</p>
        </div>
    `;
}

// ==================== STUDY BUDDY DEMO ====================
function generateDemoFlashcards(text) {
    const sentences = text.split(/[.!?]/).filter(s => s.trim().length > 10);
    const flashcards = [];
    
    for (let i = 0; i < Math.min(3, sentences.length); i++) {
        const sentence = sentences[i].trim();
        const words = sentence.split(' ');
        
        if (words.length > 4) {
            flashcards.push({
                question: `What is the main idea about "${words.slice(0, 3).join(' ')}..."?`,
                answer: sentence
            });
        }
    }
    
    if (flashcards.length === 0) {
        flashcards.push({
            question: 'What is the main topic of your text?',
            answer: text.substring(0, 200) + (text.length > 200 ? '...' : '')
        });
    }
    
    return flashcards;
}

// ==================== MOOD JOURNAL DEMO ====================
function analyzeDemoSentiment(text) {
    const positiveWords = ['happy', 'good', 'great', 'love', 'excited', 'wonderful', 'amazing', 'joy'];
    const negativeWords = ['sad', 'bad', 'angry', 'hate', 'terrible', 'awful', 'stress', 'tired'];
    
    const textLower = text.toLowerCase();
    let positiveCount = 0;
    let negativeCount = 0;
    
    positiveWords.forEach(word => { if (textLower.includes(word)) positiveCount++; });
    negativeWords.forEach(word => { if (textLower.includes(word)) negativeCount++; });
    
    if (positiveCount > negativeCount) return { sentiment: 'positive', score: (70 + Math.random() * 25).toFixed(1) };
    if (negativeCount > positiveCount) return { sentiment: 'negative', score: (70 + Math.random() * 25).toFixed(1) };
    return { sentiment: 'neutral', score: (40 + Math.random() * 30).toFixed(1) };
}

// ==================== RECIPE FINDER DEMO ====================
function generateDemoRecipes(ingredients) {
    const ingredientList = ingredients.split(',').map(i => i.trim());
    return `
Recipe 1: ${ingredientList[0] || 'Main'} Dish
A simple and delicious dish using ${ingredients}
Instructions:
1. Prepare all ingredients
2. Cook with your preferred method
3. Season to taste
4. Serve hot

Recipe 2: ${ingredientList[1] || 'Side'} Salad
A fresh salad featuring ${ingredients}
Instructions:
1. Chop ingredients
2. Mix together
3. Add dressing
4. Serve chilled

Nutrition: Rich in vitamins and minerals. Demo mode - actual recipes require backend.
`;
}

// ==================== UPDATED STUDY BUDDY ====================
async function generateFlashcards() {
    const text = document.getElementById('studyText').value.trim();
    if (!text) {
        showError('studyResults', 'Please enter some study text');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });

        if (!response.ok && !isLocal) {
            const demoFlashcards = generateDemoFlashcards(text);
            displayFlashcards(demoFlashcards);
            return;
        }

        const data = await response.json();
        if (data.error) {
            showError('studyResults', data.error);
        } else {
            displayFlashcards(data.flashcards);
        }
    } catch (error) {
        if (!isLocal) {
            const demoFlashcards = generateDemoFlashcards(text);
            displayFlashcards(demoFlashcards);
        } else {
            showError('studyResults', 'Failed to generate flashcards. Make sure the backend server is running.');
        }
    }
}

// ==================== UPDATED MOOD JOURNAL ====================
async function addMoodEntry() {
    const text = document.getElementById('moodText').value.trim();
    if (!text) {
        showError('moodResults', 'Please enter your feelings');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/mood/entry`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });

        if (!response.ok && !isLocal) {
            const demoAnalysis = analyzeDemoSentiment(text);
            showDemoMoodResult(demoAnalysis);
            return;
        }

        const data = await response.json();
        if (data.success) {
            showMoodResult(data);
        } else {
            showError('moodResults', data.error || 'Analysis failed');
        }
    } catch (error) {
        if (!isLocal) {
            const demoAnalysis = analyzeDemoSentiment(text);
            showDemoMoodResult(demoAnalysis);
        } else {
            showError('moodResults', 'Failed to analyze mood. Make sure the backend server is running.');
        }
    }
}

function showDemoMoodResult(analysis) {
    const container = document.getElementById('moodResults');
    container.innerHTML = `
        <div class="mood-result">
            <h3>Demo Mood Analysis 🎭</h3>
            <p>Sentiment: <strong>${analysis.sentiment}</strong></p>
            <p>Score: <span class="sentiment-score">${analysis.score}%</span></p>
            <p class="success">This is a demonstration. Actual AI analysis requires backend deployment.</p>
        </div>
    `;
}

// ==================== UPDATED RECIPE FINDER ====================
async function generateRecipes() {
    const ingredients = document.getElementById('ingredients').value.trim();
    if (!ingredients) {
        showError('recipeResults', 'Please enter some ingredients');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/recipes/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ingredients: ingredients })
        });

        if (!response.ok && !isLocal) {
            const demoRecipes = generateDemoRecipes(ingredients);
            displayRecipes(demoRecipes);
            return;
        }

        const data = await response.json();
        if (data.success) {
            displayRecipes(data.recipes);
        } else {
            showError('recipeResults', data.error || 'Recipe generation failed');
        }
    } catch (error) {
        if (!isLocal) {
            const demoRecipes = generateDemoRecipes(ingredients);
            displayRecipes(demoRecipes);
        } else {
            showError('recipeResults', 'Failed to generate recipes. Make sure the backend server is running.');
        }
    }
}

// ==================== UPDATE LOAD FUNCTIONS TOO ====================
async function loadMoodEntries() {
    if (!isLocal) {
        showDemoMessage('allMoodEntries', 'Mood history requires backend deployment.');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/mood/entries`);
        const data = await response.json();
        if (data.error) showError('allMoodEntries', data.error);
        else displayMoodEntries(data.entries);
    } catch (error) {
        showError('allMoodEntries', 'Failed to load mood entries');
    }
}

async function loadRecipes() {
    if (!isLocal) {
        showDemoMessage('allRecipes', 'Saved recipes require backend deployment.');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/recipes`);
        const data = await response.json();
        if (data.error) showError('allRecipes', data.error);
        else displayAllRecipes(data.recipes);
    } catch (error) {
        showError('allRecipes', 'Failed to load recipes');
    }
}

