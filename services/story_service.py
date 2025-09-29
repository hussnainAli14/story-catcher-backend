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
                return "What led up to that moment? Were you rushing somewhere, feeling distracted, or was it just an ordinary day that suddenly changed?"
            elif any(word in first_answer for word in ['lost', 'death', 'died', 'passed away']):
                return "What led up to that moment? What was happening in your life before this loss occurred?"
            elif any(word in first_answer for word in ['job', 'work', 'career', 'fired', 'quit', 'resigned']):
                return "What led up to that moment? What was happening at work or in your career before this change?"
            elif any(word in first_answer for word in ['relationship', 'breakup', 'divorce', 'marriage', 'love']):
                return "What led up to that moment? What was happening in your relationship before this change?"
            elif any(word in first_answer for word in ['move', 'moved', 'relocated', 'travel', 'journey']):
                return "What led up to that moment? What circumstances led to this change in your life?"
            else:
                return "What led up to that moment? What was happening in your life before this experience occurred?"
        
        # Question 3: What happened right after?
        elif question_number == 3:
            if any(word in first_answer for word in ['fell', 'fall', 'accident', 'crash', 'collision']):
                return "What happened right after you fell? How did you feel — physically and emotionally — in those first moments? Did someone help you?"
            elif any(word in first_answer for word in ['lost', 'death', 'died', 'passed away']):
                return "What happened right after you learned about this loss? How did you feel in those first moments? Who was there with you?"
            elif any(word in first_answer for word in ['job', 'work', 'career', 'fired', 'quit', 'resigned']):
                return "What happened right after this career change? How did you feel in those first moments? What did you do next?"
            elif any(word in first_answer for word in ['relationship', 'breakup', 'divorce', 'marriage', 'love']):
                return "What happened right after this relationship change? How did you feel in those first moments? What did you do next?"
            elif any(word in first_answer for word in ['move', 'moved', 'relocated', 'travel', 'journey']):
                return "What happened right after this change? How did you feel in those first moments? What was it like to be in this new situation?"
            else:
                return "What happened right after this experience? How did you feel in those first moments? What was going through your mind?"
        
        # Question 4: How did this change you?
        elif question_number == 4:
            if any(word in first_answer for word in ['fell', 'fall', 'accident', 'crash', 'collision']):
                return "How did this moment change you? Did it shift how you think, act, or feel in your daily life? Maybe it made you more careful or more aware of your surroundings?"
            elif any(word in first_answer for word in ['lost', 'death', 'died', 'passed away']):
                return "How did this loss change you? Did it shift how you think about life, relationships, or what matters most to you?"
            elif any(word in first_answer for word in ['job', 'work', 'career', 'fired', 'quit', 'resigned']):
                return "How did this career change transform you? Did it shift how you think about work, success, or your life priorities?"
            elif any(word in first_answer for word in ['relationship', 'breakup', 'divorce', 'marriage', 'love']):
                return "How did this relationship change transform you? Did it shift how you think about love, connection, or what you want in relationships?"
            elif any(word in first_answer for word in ['move', 'moved', 'relocated', 'travel', 'journey']):
                return "How did this change transform you? Did it shift how you think about home, belonging, or what you value in life?"
            else:
                return "How did this experience change you? Did it shift how you think, act, or feel in your daily life? What stayed with you after this moment?"
        
        return ""
    
    def _generate_contextual_feedback(self, question_number, answer_text):
        """Generate contextual feedback based on the answer content"""
        answer_lower = answer_text.lower()
        
        if question_number == 1:
            if any(word in answer_lower for word in ['fell', 'fall', 'accident', 'crash', 'collision']):
                return "Thank you for sharing that — falling down the stairs can be incredibly frightening, both physically and emotionally. I'm glad you're here to talk about it. You're safe now, and we're going to take this story gently, step by step."
            elif any(word in answer_lower for word in ['lost', 'death', 'died', 'passed away']):
                return "Thank you for sharing that with me. Loss can be one of the most profound experiences we face. I'm honored that you're willing to talk about this moment with me."
            elif any(word in answer_lower for word in ['job', 'work', 'career', 'fired', 'quit', 'resigned']):
                return "Thank you for sharing that experience. Career changes can be both exciting and terrifying. I can hear how significant this moment was for you."
            elif any(word in answer_lower for word in ['relationship', 'breakup', 'divorce', 'marriage', 'love']):
                return "Thank you for sharing that. Relationships touch the deepest parts of who we are. I can hear how meaningful this moment was for you."
            else:
                return "Thank you for sharing that experience with me. I can hear how significant this moment was for you."
        
        elif question_number == 2:
            if any(word in answer_lower for word in ['phone', 'distracted', 'rushing', 'hurried']):
                return "Thank you — that adds a lot of emotional weight to the moment. Feeling distracted, being on your phone… it makes the experience even more relatable and human."
            elif any(word in answer_lower for word in ['ordinary', 'normal', 'regular', 'typical']):
                return "Thank you for sharing that. Sometimes the most profound moments happen on the most ordinary days. That contrast can make the experience even more powerful."
            else:
                return "Thank you for sharing those details. Understanding what led up to the moment helps us see the full picture of your experience."
        
        elif question_number == 3:
            if any(word in answer_lower for word in ['hurt', 'pain', 'injured', 'bruised']):
                return "That must've been such a disorienting and jarring few moments — a mix of pain, confusion, and sudden awareness. Those brief moments can feel like they stretch forever."
            elif any(word in answer_lower for word in ['help', 'helped', 'someone', 'people']):
                return "Thank you for sharing that. It's so important to have people there for us in those difficult moments. I'm glad you weren't alone."
            else:
                return "Thank you for sharing those details. Those first moments after something significant happens can be so intense and confusing."
        
        return "Thank you for sharing that with me."
    
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
                    'category': question.category
                })
            except StopIteration:
                print(f"Question with ID {answer.question_id} not found")
                # Fallback for missing questions
                formatted_answers.append({
                    'question': f"Question {answer.question_id}",
                    'answer': answer.answer_text,
                    'category': 'unknown'
                })
        
        print(f"Formatted {len(formatted_answers)} answers for story generation")
        return formatted_answers
