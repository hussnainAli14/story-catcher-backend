from models.story_models import StorySession, Question, Answer
from datetime import datetime
import uuid

class StoryService:
    def __init__(self):
        # In-memory storage for demo purposes
        # In production, you'd use a database
        self.sessions = {}
        self.questions = self._initialize_questions()
    
    def _initialize_questions(self):
        """Initialize the dynamic story questions"""
        return [
            Question(
                id=1,
                text="What was the life-changing moment you experienced?",
                category="core_experience",
                order=1
            ),
            Question(
                id=2,
                text="",  # Will be dynamically generated
                category="contextual_setup",
                order=2
            ),
            Question(
                id=3,
                text="",  # Will be dynamically generated
                category="contextual_aftermath",
                order=3
            ),
            Question(
                id=4,
                text="",  # Will be dynamically generated
                category="contextual_transformation",
                order=4
            )
        ]
    
    def create_new_session(self):
        """Create a new story session"""
        session_id = str(uuid.uuid4())
        session = StorySession(
            session_id=session_id,
            created_at=datetime.now(),
            answers=[],
            current_question=1,
            is_complete=False
        )
        self.sessions[session_id] = session
        return session
    
    def get_next_question(self, session_id):
        """Get the next question for a session"""
        if session_id not in self.sessions:
            raise ValueError("Session not found")
        
        session = self.sessions[session_id]
        
        if session.current_question > len(self.questions):
            return None
        
        question = self.questions[session.current_question - 1]
        
        # Generate contextual question if it's empty
        if not question.text and session.current_question > 1:
            question.text = self._generate_contextual_question(session.current_question, session.answers)
        
        return {
            'id': question.id,
            'text': question.text,
            'category': question.category,
            'order': question.order
        }
    
    def _generate_contextual_question(self, question_number, answers):
        """Generate contextual questions based on previous answers"""
        if not answers:
            return ""
        
        first_answer = answers[0].answer_text.lower()
        
        # Question 2: What led up to that moment?
        if question_number == 2:
            if any(word in first_answer for word in ['fell', 'fall', 'accident', 'crash', 'collision']):
                return "I can only imagine how frightening that must have been. Before we continue, I want you to know this is a safe space to share whatever feels right to you. What led up to that moment? Were you rushing somewhere, feeling distracted, or was it just an ordinary day that suddenly changed? Take your time with this."
            elif any(word in first_answer for word in ['lost', 'death', 'died', 'passed away']):
                return "Thank you for trusting me with something so deeply personal. Loss can be one of the most profound experiences we face. What led up to that moment? What was happening in your life before this loss occurred? I'm here to listen, and there's no rush."
            elif any(word in first_answer for word in ['job', 'work', 'career', 'fired', 'quit', 'resigned']):
                return "Career changes can be both exciting and terrifying. I can hear how significant this moment was for you. What led up to that moment? What was happening at work or in your career before this change? How are you feeling as you share this?"
            elif any(word in first_answer for word in ['relationship', 'breakup', 'divorce', 'marriage', 'love']):
                return "Relationships touch the deepest parts of who we are. Thank you for sharing something so meaningful. What led up to that moment? What was happening in your relationship before this change? I'm here to listen with compassion."
            elif any(word in first_answer for word in ['move', 'moved', 'relocated', 'travel', 'journey']):
                return "Life changes like moving can be both exciting and overwhelming. What led up to that moment? What circumstances led to this change in your life? Take your time to share whatever feels important to you."
            else:
                return "Thank you for sharing that with me. I can hear how significant this moment was for you. What led up to that moment? What was happening in your life before this experience occurred? There's no right or wrong way to answer this."
        
        # Question 3: What happened right after?
        elif question_number == 3:
            if any(word in first_answer for word in ['fell', 'fall', 'accident', 'crash', 'collision']):
                return "That must have been such a disorienting and jarring few moments. How are you feeling as you share this? What happened right after you fell? How did you feel — physically and emotionally — in those first moments? Did someone help you? It's okay if this brings up difficult emotions."
            elif any(word in first_answer for word in ['lost', 'death', 'died', 'passed away']):
                return "I can only imagine how overwhelming those first moments must have been. How are you doing as you share this? What happened right after you learned about this loss? How did you feel in those first moments? Who was there with you? Take breaks whenever you need to."
            elif any(word in first_answer for word in ['job', 'work', 'career', 'fired', 'quit', 'resigned']):
                return "Career changes can feel like your whole world is shifting. How are you feeling about sharing this? What happened right after this career change? How did you feel in those first moments? What did you do next? I'm here to listen without judgment."
            elif any(word in first_answer for word in ['relationship', 'breakup', 'divorce', 'marriage', 'love']):
                return "Relationship changes can feel like the ground is moving beneath you. How are you feeling as you share this? What happened right after this relationship change? How did you feel in those first moments? What did you do next? Your feelings are completely valid."
            elif any(word in first_answer for word in ['move', 'moved', 'relocated', 'travel', 'journey']):
                return "Big life changes can be both exciting and overwhelming. How are you feeling about sharing this? What happened right after this change? How did you feel in those first moments? What was it like to be in this new situation? Take your time."
            else:
                return "Thank you for continuing to share your story with me. How are you feeling as we explore this? What happened right after this experience? How did you feel in those first moments? What was going through your mind? There's no rush, and we can pause anytime."
        
        # Question 4: How did this change you?
        elif question_number == 4:
            if any(word in first_answer for word in ['fell', 'fall', 'accident', 'crash', 'collision']):
                return "I can hear the strength it took to get through that experience. How are you feeling as we near the end of our conversation? How did this moment change you? Did it shift how you think, act, or feel in your daily life? Maybe it made you more careful or more aware of your surroundings? Your growth is beautiful to witness."
            elif any(word in first_answer for word in ['lost', 'death', 'died', 'passed away']):
                return "Thank you for trusting me with something so deeply personal. How are you feeling as we explore this? How did this loss change you? Did it shift how you think about life, relationships, or what matters most to you? Your courage in sharing this is inspiring."
            elif any(word in first_answer for word in ['job', 'work', 'career', 'fired', 'quit', 'resigned']):
                return "Career changes can be profound teachers. How are you feeling about sharing this journey? How did this career change transform you? Did it shift how you think about work, success, or your life priorities? Your resilience is evident."
            elif any(word in first_answer for word in ['relationship', 'breakup', 'divorce', 'marriage', 'love']):
                return "Relationship changes can teach us so much about ourselves. How are you feeling as we explore this? How did this relationship change transform you? Did it shift how you think about love, connection, or what you want in relationships? Your openness is beautiful."
            elif any(word in first_answer for word in ['move', 'moved', 'relocated', 'travel', 'journey']):
                return "Life changes like moving can be incredible catalysts for growth. How are you feeling about sharing this? How did this change transform you? Did it shift how you think about home, belonging, or what you value in life? Your adaptability is inspiring."
            else:
                return "Thank you for sharing your story with such openness and courage. How are you feeling as we explore this final question? How did this experience change you? Did it shift how you think, act, or feel in your daily life? What stayed with you after this moment? Your willingness to reflect deeply is beautiful."
        
        return ""
    
    def _generate_contextual_feedback(self, question_number, answer_text):
        """Generate contextual feedback based on the answer content"""
        answer_lower = answer_text.lower()
        
        if question_number == 1:
            if any(word in answer_lower for word in ['fell', 'fall', 'accident', 'crash', 'collision']):
                return "Thank you for sharing that with such courage. Falling down the stairs can be incredibly frightening, both physically and emotionally. I'm honored that you're willing to talk about it with me. You're safe now, and we're going to take this story gently, step by step. How are you feeling as you share this?"
            elif any(word in answer_lower for word in ['lost', 'death', 'died', 'passed away']):
                return "Thank you for trusting me with something so deeply personal. Loss can be one of the most profound experiences we face, and I'm honored that you're willing to talk about this moment with me. Your courage in sharing this is beautiful. How are you feeling as you share this?"
            elif any(word in answer_lower for word in ['job', 'work', 'career', 'fired', 'quit', 'resigned']):
                return "Thank you for sharing that experience with such openness. Career changes can be both exciting and terrifying, and I can hear how significant this moment was for you. Your willingness to reflect on this is inspiring. How are you feeling about sharing this?"
            elif any(word in answer_lower for word in ['relationship', 'breakup', 'divorce', 'marriage', 'love']):
                return "Thank you for sharing that with such vulnerability. Relationships touch the deepest parts of who we are, and I can hear how meaningful this moment was for you. Your openness is beautiful. How are you feeling as you share this?"
            else:
                return "Thank you for sharing that experience with such courage. I can hear how significant this moment was for you, and I'm honored that you're willing to explore it with me. How are you feeling about sharing this?"
        
        elif question_number == 2:
            if any(word in answer_lower for word in ['phone', 'distracted', 'rushing', 'hurried']):
                return "Thank you for sharing those details — that adds so much emotional weight to the moment. Feeling distracted, being on your phone… it makes the experience even more relatable and human. I can hear how that context made everything feel more intense. How are you feeling as you share this?"
            elif any(word in answer_lower for word in ['ordinary', 'normal', 'regular', 'typical']):
                return "Thank you for sharing that. Sometimes the most profound moments happen on the most ordinary days, and that contrast can make the experience even more powerful. I can hear how unexpected it all was. How are you feeling about sharing this?"
            else:
                return "Thank you for sharing those details with such thoughtfulness. Understanding what led up to the moment helps us see the full picture of your experience, and I can hear how important that context is. How are you feeling as you share this?"
        
        elif question_number == 3:
            if any(word in answer_lower for word in ['hurt', 'pain', 'injured', 'bruised']):
                return "Thank you for sharing those details. That must've been such a disorienting and jarring few moments — a mix of pain, confusion, and sudden awareness. Those brief moments can feel like they stretch forever, and I can hear how intense that was for you. How are you feeling as you share this?"
            elif any(word in answer_lower for word in ['help', 'helped', 'someone', 'people']):
                return "Thank you for sharing that. It's so important to have people there for us in those difficult moments, and I'm glad you weren't alone. I can hear how much that support meant to you. How are you feeling about sharing this?"
            else:
                return "Thank you for sharing those details with such openness. Those first moments after something significant happens can be so intense and confusing, and I can hear how overwhelming that was. How are you feeling as you share this?"
        
        return "Thank you for sharing that with me. How are you feeling about our conversation so far?"
    
    def save_answer(self, session_id, question_number, answer_text):
        """Save an answer to a question"""
        if session_id not in self.sessions:
            raise ValueError("Session not found")
        
        session = self.sessions[session_id]
        
        # Create answer object
        answer = Answer(
            question_id=question_number,
            answer_text=answer_text,
            timestamp=datetime.now()
        )
        
        # Add answer to session
        session.answers.append(answer)
        
        # Update current question
        session.current_question = question_number + 1
        
        # Check if session is complete
        if len(session.answers) >= 4:
            session.is_complete = True
    
    def get_session_data(self, session_id):
        """Get complete session data"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        return session.to_dict()
    
    def get_all_answers_for_story_generation(self, session_id):
        """Get formatted answers for story generation"""
        if session_id not in self.sessions:
            print(f"Session {session_id} not found in sessions")
            return None
        
        session = self.sessions[session_id]
        print(f"Session has {len(session.answers)} answers")
        
        # Format answers with questions for context
        formatted_answers = []
        for answer in session.answers:
            try:
                question = next(q for q in self.questions if q.id == answer.question_id)
                formatted_answers.append({
                    'question': question.text,
                    'answer': answer.answer_text,
                    'category': question.category,
                    'session_id': session_id
                })
            except StopIteration:
                print(f"Question with ID {answer.question_id} not found")
                # Fallback for missing questions
                formatted_answers.append({
                    'question': f"Question {answer.question_id}",
                    'answer': answer.answer_text,
                    'category': 'unknown',
                    'session_id': session_id
                })
        
        print(f"Formatted {len(formatted_answers)} answers for story generation")
        return formatted_answers
    
    def save_generated_storyboard(self, session_id, storyboard):
        """Save the generated storyboard to the session"""
        if session_id not in self.sessions:
            print(f"Session {session_id} not found")
            return False
        
        session = self.sessions[session_id]
        session.generated_story = storyboard
        print(f"Saved storyboard for session {session_id}")
        return True
    
    def get_generated_storyboard(self, session_id):
        """Get the generated storyboard from the session"""
        if session_id not in self.sessions:
            print(f"Session {session_id} not found")
            return None
        
        session = self.sessions[session_id]
        return session.generated_story
    
    def save_user_email(self, session_id, email):
        """Save user email to the session"""
        print(f"Attempting to save email {email} for session {session_id}")
        print(f"Available sessions: {list(self.sessions.keys())}")
        
        if session_id not in self.sessions:
            print(f"Session {session_id} not found in sessions")
            return False
        
        session = self.sessions[session_id]
        session.user_email = email
        print(f"Successfully saved email {email} for session {session_id}")
        return True
    
    def save_to_supabase(self, session_id, video_url):
        """Save the completed story to Supabase"""
        print(f"Attempting to save to Supabase for session {session_id} with video {video_url}")
        print(f"Available sessions: {list(self.sessions.keys())}")
        
        if session_id not in self.sessions:
            print(f"Session {session_id} not found in sessions")
            return False
        
        session = self.sessions[session_id]
        print(f"Session found, user_email: {session.user_email}")
        
        if not session.user_email:
            print(f"No email found for session {session_id}, skipping Supabase save")
            return False
        
        try:
            import os
            from supabase import create_client
            
            # Get Supabase client
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            
            print(f"Supabase URL: {supabase_url}")
            print(f"Supabase Key: {supabase_key[:10]}..." if supabase_key else "None")
            
            if not supabase_url or not supabase_key:
                print("Supabase credentials not found")
                return False
            
            supabase = create_client(supabase_url, supabase_key)
            
            # Prepare data for Supabase
            data_to_insert = {
                'email': session.user_email,
                'video_url': video_url,
                'created_at': session.created_at.isoformat()
            }
            print(f"Data to insert: {data_to_insert}")
            
            # Save to Supabase
            response = supabase.table('story_submissions').insert([data_to_insert]).execute()
            
            print(f"Supabase response: {response}")
            print(f"Successfully saved story to Supabase for session {session_id}")
            return True
            
        except Exception as e:
            print(f"Error saving to Supabase: {e}")
            return False
