from flask import Flask, request, jsonify
from flask-cors import CORS
import mysql.connector
import os
import random
from dotenv import load_dotenv
import re
import requests
import openai
from datetime import datetime

# Load the secrets from the .env file into our environment
load_dotenv()

# Create the main Flask application object
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins for development

# Configuration for connecting to the MySQL database
db_config = {
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': 'study_buddy'
}

# API Configurations
HF_SENTIMENT_API = "https://api-inference.huggingface.co/models/j-hartmann/emotion-english-distilroberta-base"
HF_API_KEY = os.getenv('HF_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None

def initialize_database():
    """Create tables if they don't exist"""
    try:
        conn = get_db_connection()
        if conn is None:
            print("Failed to connect to database")
            return False
            
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute("CREATE DATABASE IF NOT EXISTS study_buddy")
        cursor.execute("USE study_buddy")
        
        # Create flashcard_sets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS flashcard_sets (
                id INT AUTO_INCREMENT PRIMARY KEY,
                original_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create flashcards table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS flashcards (
                id INT AUTO_INCREMENT PRIMARY KEY,
                set_id INT,
                question TEXT,
                answer TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (set_id) REFERENCES flashcard_sets(id) ON DELETE CASCADE
            )
        """)
        
        # Create mood journal table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INT AUTO_INCREMENT PRIMARY KEY,
                entry_text TEXT,
                sentiment_score FLOAT,
                emotion_label VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create recipes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ingredients TEXT,
                recipe_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Database tables initialized successfully")
        return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False

# ==================== STUDY BUDDY FUNCTIONS ====================
def generate_flashcards_from_text(text):
    """Generate multiple flashcards from input text using rule-based patterns"""
    flashcards = []
    
    # Clean and split the text into sentences
    sentences = re.split(r'[.!?]', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    
    for sentence in sentences:
        if not sentence:
            continue
            
        # Try different question generation patterns
        question, answer = generate_question_answer(sentence)
        if question and answer:
            flashcards.append({'question': question, 'answer': answer})
    
    # If no good flashcards generated, create a default one
    if not flashcards:
        question = f"What is the main topic of: {text[:100]}..."
        answer = text[:200] + "..." if len(text) > 200 else text
        flashcards.append({'question': question, 'answer': answer})
    
    return flashcards[:5]  # Limit to 5 flashcards

def generate_question_answer(sentence):
    """Generate a question and answer pair from a sentence"""
    sentence_lower = sentence.lower()
    
    # Pattern 1: Definitions (X is Y)
    if re.search(r'\bis\b', sentence_lower):
        match = re.search(r'(\w[\w\s]+)\s+is\s+([^.!?]+)', sentence, re.IGNORECASE)
        if match:
            term = match.group(1).strip()
            definition = match.group(2).strip()
            question = f"What is {term}?"
            answer = definition
            return question, answer
    
    # Pattern 2: Dates and events
    date_match = re.search(r'(\b\d{4}\b)', sentence)
    if date_match:
        year = date_match.group(1)
        question = f"What happened in {year}?"
        answer = sentence
        return question, answer
    
    # Pattern 3: Causes and effects
    if ' because ' in sentence_lower:
        parts = sentence.split(' because ', 1)
        if len(parts) == 2:
            effect = parts[0].strip()
            cause = parts[1].strip()
            question = f"Why {effect}?"
            answer = f"Because {cause}"
            return question, answer
    
    # Pattern 4: Lists and items
    if re.search(r'\b(including|such as|e\.g\.|for example)\b', sentence_lower):
        question = f"What are some examples from: {sentence[:80]}..."
        answer = sentence
        return question, answer
    
    # Pattern 5: Convert statement to question
    words = sentence.split()
    if len(words) > 4:
        if words[0].lower() in ['the', 'a', 'an']:
            question = f"What is {sentence}?"
        else:
            question = f"What does this describe: {sentence}?"
        answer = sentence
        return question, answer
    
    return None, None

@app.route('/generate', methods=['POST'])
def generate_flashcards():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
        
    study_text = data.get('text', '')
    
    if not study_text:
        return jsonify({'error': 'No text provided'}), 400

    try:
        flashcards_data = generate_flashcards_from_text(study_text)
        
        # Save to database if connection is available
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO flashcard_sets (original_text) VALUES (%s)", (study_text,))
            set_id = cursor.lastrowid

            for flashcard in flashcards_data:
                cursor.execute("INSERT INTO flashcards (set_id, question, answer) VALUES (%s, %s, %s)",
                               (set_id, flashcard['question'], flashcard['answer']))
            
            conn.commit()
            cursor.close()
            conn.close()

        return jsonify({
            'flashcards': flashcards_data, 
            'message': f'Generated {len(flashcards_data)} flashcards!'
        })

    except Exception as e:
        print(f"Error in generate_flashcards: {e}")
        return jsonify({'error': 'Failed to generate flashcards'}), 500

# ==================== MOOD JOURNAL FUNCTIONS ====================
def analyze_sentiment(text):
    """Analyze sentiment with fallback to simple rule-based analysis"""
    # Try Hugging Face API first if available
    if HF_API_KEY:
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        try:
            response = requests.post(HF_SENTIMENT_API, headers=headers, 
                                   json={"inputs": text}, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result
        except Exception as e:
            print(f"Hugging Face API error: {e}")
    
    # Fallback: Simple rule-based sentiment analysis
    positive_words = ['happy', 'good', 'great', 'wonderful', 'excellent', 'joy', 'love', 'amazing']
    negative_words = ['sad', 'bad', 'terrible', 'awful', 'horrible', 'angry', 'hate', 'disappointing']
    
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    if positive_count > negative_count:
        return [{'label': 'positive', 'score': 0.7 + (positive_count * 0.05)}]
    elif negative_count > positive_count:
        return [{'label': 'negative', 'score': 0.7 + (negative_count * 0.05)}]
    else:
        return [{'label': 'neutral', 'score': 0.5}]

@app.route('/mood/entry', methods=['POST'])
def add_mood_entry():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
        
    entry_text = data.get('text', '')
    
    if not entry_text:
        return jsonify({'error': 'No journal entry provided'}), 400
    
    # Analyze sentiment
    sentiment_result = analyze_sentiment(entry_text)
    sentiment_score = 0.5
    emotion_label = "neutral"
    
    if sentiment_result and isinstance(sentiment_result, list):
        emotions = sentiment_result[0]
        if isinstance(emotions, dict):
            top_emotion = max(emotions, key=lambda x: x['score']) if isinstance(emotions, list) else emotions
            emotion_label = top_emotion.get('label', 'neutral')
            sentiment_score = top_emotion.get('score', 0.5)
    
    # Save to database
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO journal_entries (entry_text, sentiment_score, emotion_label) VALUES (%s, %s, %s)",
                (entry_text, sentiment_score, emotion_label)
            )
            conn.commit()
            cursor.close()
            conn.close()
        
        return jsonify({
            'success': True,
            'sentiment': emotion_label,
            'score': round(sentiment_score * 100, 1),
            'message': 'Mood entry saved successfully'
        })
        
    except Exception as e:
        print(f"Error saving mood entry: {e}")
        return jsonify({'error': 'Failed to save mood entry'}), 500

@app.route('/mood/entries', methods=['GET'])
def get_mood_entries():
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({'entries': []})
            
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM journal_entries ORDER BY created_at DESC")
        entries = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Format dates for frontend
        for entry in entries:
            if 'created_at' in entry and entry['created_at']:
                entry['created_at'] = entry['created_at'].isoformat()
                
        return jsonify({'entries': entries})
    except Exception as e:
        print(f"Error fetching mood entries: {e}")
        return jsonify({'entries': []})

# ==================== RECIPE FINDER FUNCTIONS ====================
def generate_recipes(ingredients):
    """Generate recipes using OpenAI or fallback to template"""
    if not OPENAI_API_KEY:
        # Fallback template recipes
        recipes = [
            f"Recipe 1: {ingredients.title()} Salad|"
            f"A fresh salad using {ingredients}|"
            f"1. Chop all ingredients\n2. Mix together\n3. Add dressing\n4. Serve chilled|"
            f"High in vitamins and fiber",
            
            f"Recipe 2: {ingredients.title()} Stir Fry|"
            f"A quick stir fry with {ingredients}|"
            f"1. Heat oil in pan\n2. Add ingredients\n3. Stir fry for 5-7 minutes\n4. Season to taste|"
            f"Low calorie, high protein"
        ]
        return "\n".join(recipes)
    
    try:
        prompt = f"Suggest 2 simple, healthy recipes using: {ingredients}. Format as: Recipe 1: Name|Description|Instructions|Nutrition Benefits"
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI error: {e}")
        return "Recipe generation unavailable. Please check your API key."

@app.route('/recipes/generate', methods=['POST'])
def generate_recipe():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
        
    ingredients = data.get('ingredients', '')
    
    if not ingredients:
        return jsonify({'error': 'No ingredients provided'}), 400
    
    recipes_text = generate_recipes(ingredients)
    
    # Save to database
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO recipes (ingredients, recipe_text) VALUES (%s, %s)",
                (ingredients, recipes_text)
            )
            conn.commit()
            cursor.close()
            conn.close()
        
        return jsonify({
            'success': True,
            'recipes': recipes_text,
            'message': 'Recipes generated successfully'
        })
        
    except Exception as e:
        print(f"Error saving recipe: {e}")
        return jsonify({'error': 'Failed to save recipe'}), 500

@app.route('/recipes', methods=['GET'])
def get_recipes():
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({'recipes': []})
            
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM recipes ORDER BY created_at DESC LIMIT 5")
        recipes = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Format dates for frontend
        for recipe in recipes:
            if 'created_at' in recipe and recipe['created_at']:
                recipe['created_at'] = recipe['created_at'].isoformat()
                
        return jsonify({'recipes': recipes})
    except Exception as e:
        print(f"Error fetching recipes: {e}")
        return jsonify({'recipes': []})

# ==================== TEST ENDPOINTS ====================
@app.route('/test', methods=['GET'])
def test_endpoint():
    return jsonify({
        'message': 'Flask server is working!',
        'database_connected': get_db_connection() is not None,
        'openai_available': bool(OPENAI_API_KEY),
        'hf_available': bool(HF_API_KEY)
    })

@app.route('/test-generate', methods=['GET'])
def test_generate():
    test_text = "Photosynthesis is the process by which plants convert sunlight into energy. This happens because chlorophyll captures light energy. The French Revolution occurred in 1789 and changed European history forever."
    flashcards = generate_flashcards_from_text(test_text)
    return jsonify({'test_flashcards': flashcards})

@app.route('/test-db', methods=['GET'])
def test_db():
    conn = get_db_connection()
    if conn:
        conn.close()
        return jsonify({'status': 'Database connection successful'})
    else:
        return jsonify({'error': 'Database connection failed'})

if __name__ == '__main__':
    import os
    initialize_database()
    port = int(os.environ.get('PORT', 5000))
    print(f"Server starting on http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
    print("=" * 50)
    print("MerciAI Study Platform Server")
    print("=" * 50)
    print(f"Database initialized: {db_initialized}")
    print(f"OpenAI API available: {bool(OPENAI_API_KEY)}")
    print(f"Hugging Face API available: {bool(HF_API_KEY)}")
    print("\nEndpoints:")
    print("Study Buddy: POST /generate")
    print("Mood Journal: POST /mood/entry, GET /mood/entries")
    print("Recipe Finder: POST /recipes/generate, GET /recipes")
    print("Test: GET /test, GET /test-generate, GET /test-db")
    print("\nServer starting on http://localhost:5000")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
   