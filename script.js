// Study Buddy Functions
async function generateFlashcards() {
    const studyText = document.getElementById('studyText').value;
    const button = event.target;
    button.textContent = "Generating...";
    button.disabled = true;

    try {
        const response = await fetch('http://127.0.0.1:5000/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: studyText })
        });

        const data = await response.json();
        if (response.ok) {
            displayFlashcards(data.flashcards);
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to connect to the server.');
    } finally {
        button.textContent = "Generate Flashcards";
        button.disabled = false;
    }
}

function displayFlashcards(flashcards) {
    const container = document.getElementById('flashcardsContainer');
    container.innerHTML = ''; // Clear previous cards

    flashcards.forEach(cardData => {
        const card = document.createElement('div');
        card.className = 'flashcard';
        card.innerHTML = `
            <div class="flashcard-inner">
                <div class="flashcard-front">
                    <p><strong>Q:</strong> ${cardData.question}</p>
                </div>
                <div class="flashcard-back">
                    <p><strong>A:</strong> ${cardData.answer}</p>
                </div>
            </div>
        `;
        card.addEventListener('click', () => {
            card.classList.toggle('flipped');
        });
        container.appendChild(card);
    });
}

// Mood Journal Functions - UPDATED
async function addMoodEntry() {
    const text = document.getElementById('moodText').value.trim();
    if (!text) {
        showError('moodResults', 'Please enter your feelings');
        return;
    }

    try {
        const response = await fetch('http://127.0.0.1:5000/mood/entry', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: text })
        });

        const data = await response.json();
        
        // FIXED: Check for the correct response structure
        if (data.success) {
            showMoodResult(data);
        } else if (data.error) {
            showError('moodResults', data.error);
        } else {
            showError('moodResults', 'Unexpected response from server');
        }
    } catch (error) {
        showError('moodResults', 'Failed to save mood entry: ' + error.message);
    }
}

function showMoodResult(data) {
    const container = document.getElementById('moodResults');
    container.innerHTML = `
        <div class="mood-result">
            <h3>Mood Analysis</h3>
            <p>Sentiment: <strong>${data.sentiment}</strong></p>
            <p>Score: <span class="sentiment-score">${data.score}%</span></p>
            <p class="success">${data.message}</p>
        </div>
    `;
}

async function loadMoodEntries() {
    try {
        const response = await fetch('http://127.0.0.1:5000/mood/entries');
        const data = await response.json();
        
        if (data.error) {
            showError('allMoodEntries', data.error);
        } else {
            displayMoodEntries(data.entries);
        }
    } catch (error) {
        showError('allMoodEntries', 'Failed to load mood entries');
    }
}

function displayMoodEntries(entries) {
    const container = document.getElementById('allMoodEntries');
    container.innerHTML = '<h3>All Mood Entries:</h3>';
    
    if (entries.length === 0) {
        container.innerHTML += '<p>No entries yet</p>';
        return;
    }
    
    entries.forEach(entry => {
        const entryDiv = document.createElement('div');
        entryDiv.className = 'flashcard';
        entryDiv.innerHTML = `
            <p><strong>Date:</strong> ${new Date(entry.created_at).toLocaleString()}</p>
            <p><strong>Entry:</strong> ${entry.entry_text}</p>
            <p><strong>Mood:</strong> ${entry.emotion_label} (${entry.sentiment_score * 100}%)</p>
        `;
        container.appendChild(entryDiv);
    });
}

// Recipe Finder Functions - UPDATED
async function generateRecipes() {
    const ingredients = document.getElementById('ingredients').value.trim();
    if (!ingredients) {
        showError('recipeResults', 'Please enter some ingredients');
        return;
    }

    try {
        const response = await fetch('http://127.0.0.1:5000/recipes/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ ingredients: ingredients })
        });

        const data = await response.json();
        
        // FIXED: Check for the correct response structure
        if (data.success) {
            displayRecipes(data.recipes);
        } else if (data.error) {
            showError('recipeResults', data.error);
        } else {
            showError('recipeResults', 'Unexpected response from server');
        }
    } catch (error) {
        showError('recipeResults', 'Failed to generate recipes: ' + error.message);
    }
}

function displayRecipes(recipesText) {
    const container = document.getElementById('recipeResults');
    container.innerHTML = '<h3>Generated Recipes:</h3>';
    
    const recipeDiv = document.createElement('div');
    recipeDiv.className = 'recipe-card';
    recipeDiv.innerHTML = `<p>${recipesText.replace(/\n/g, '<br>')}</p>`;
    container.appendChild(recipeDiv);
}

async function loadRecipes() {
    try {
        const response = await fetch('http://127.0.0.1:5000/recipes');
        const data = await response.json();
        
        if (data.error) {
            showError('allRecipes', data.error);
        } else {
            displayAllRecipes(data.recipes);
        }
    } catch (error) {
        showError('allRecipes', 'Failed to load recipes');
    }
}

function displayAllRecipes(recipes) {
    const container = document.getElementById('allRecipes');
    container.innerHTML = '<h3>Saved Recipes:</h3>';
    
    if (recipes.length === 0) {
        container.innerHTML += '<p>No recipes yet</p>';
        return;
    }
    
    recipes.forEach(recipe => {
        const recipeDiv = document.createElement('div');
        recipeDiv.className = 'recipe-card';
        recipeDiv.innerHTML = `
            <p><strong>Ingredients:</strong> ${recipe.ingredients}</p>
            <p><strong>Recipe:</strong> ${recipe.recipe_text.replace(/\n/g, '<br>')}</p>
            <p><strong>Created:</strong> ${new Date(recipe.created_at).toLocaleString()}</p>
        `;
        container.appendChild(recipeDiv);
    });
}

// Utility Functions
function showError(containerId, message) {
    const container = document.getElementById(containerId);
    container.innerHTML = `<div class="error">${message}</div>`;
}

function showSuccess(containerId, message) {
    const container = document.getElementById(containerId);
    container.innerHTML = `<div class="success">${message}</div>`;
}

// Tab Navigation
function showTab(tabName) {
    // Hide all content sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Show selected section
    document.getElementById(tabName).classList.add('active');
    
    // Update active tab
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    event.target.classList.add('active');
}