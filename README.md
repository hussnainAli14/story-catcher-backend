# Story Catcher Backend

A Flask-based backend service for capturing and generating personal stories through an interactive interview process.

## Features

- Interactive story interview with 4 core questions
- OpenAI integration for story generation
- Session management
- RESTful API endpoints

## Setup

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**

   ```bash
   cp env.example .env
   ```

   The `.env` file should contain:

   ```
   OPENAI_API_KEY=your-openai-api-key-here
   SECRET_KEY=your-secret-key-here
   ```

3. **Run the application:**

   ```bash
   python app.py
   ```

   Or use the startup script:

   ```bash
   python start.py
   ```

The server will start on `http://localhost:5000`

## Testing

Run the test script to verify everything works:

```bash
python test_api.py
```

This will test:

- Health check endpoint
- Complete story interview workflow
- Story generation with OpenAI
- Session management

## API Endpoints

### Start Story Session

- **POST** `/api/story/start`
- **Body:** `{"message": "I'm ready to tell my story"}`
- **Response:** Session ID and first question only

### Submit Answer

- **POST** `/api/story/answer`
- **Body:** `{"session_id": "...", "answer": "...", "question_number": 1}`
- **Response:** Next question (one at a time) or generated story when complete

### Get Current Question

- **GET** `/api/story/current-question/{session_id}`
- **Response:** Current question for the session

### Get Session Status

- **GET** `/api/story/session/{session_id}`
- **Response:** Complete session data

### Health Check

- **GET** `/api/health`
- **Response:** Service status

## Story Questions

The system uses **dynamic contextual questioning** that adapts based on your responses:

1. **Core Experience:** "What was the life-changing moment you experienced?" (Always the same)
2. **Contextual Setup:** "What led up to that moment?" (Adapts based on your answer)
3. **Contextual Aftermath:** "What happened right after?" (Adapts based on your experience)
4. **Contextual Transformation:** "How did this moment change you?" (Adapts based on your journey)

### Dynamic Question Examples:

**For Accidents/Falls:**

- Q2: "What led up to that moment? Were you rushing somewhere, feeling distracted, or was it just an ordinary day that suddenly changed?"
- Q3: "What happened right after you fell? How did you feel — physically and emotionally — in those first moments? Did someone help you?"
- Q4: "How did this moment change you? Did it shift how you think, act, or feel in your daily life? Maybe it made you more careful or more aware of your surroundings?"

**For Loss/Death:**

- Q2: "What led up to that moment? What was happening in your life before this loss occurred?"
- Q3: "What happened right after you learned about this loss? How did you feel in those first moments? Who was there with you?"
- Q4: "How did this loss change you? Did it shift how you think about life, relationships, or what matters most to you?"

## Storyboard Generation

After completing all 4 questions, the system generates a **visual storyboard** including:

- 4-6 distinct scenes with visual descriptions
- Mood and atmosphere details
- Sound suggestions
- Camera movements and transitions
- Creative suggestions for animation or live-action

## Project Structure

```
story-catcher-backend/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── env.example           # Environment variables template
├── routes/
│   ├── __init__.py
│   └── story_routes.py   # API endpoints
├── models/
│   ├── __init__.py
│   └── story_models.py   # Data models
└── services/
    ├── __init__.py
    ├── story_service.py  # Business logic
    └── openai_service.py # OpenAI integration
```
