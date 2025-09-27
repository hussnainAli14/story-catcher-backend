from flask import Blueprint, request, jsonify
from services.story_service import StoryService
from services.openai_service import OpenAIService
from services.videogen_service import VideoGenService
from models.story_models import StorySession, Question, StoryResponse
import json

story_bp = Blueprint('story', __name__)

# Initialize services
story_service = StoryService()
openai_service = OpenAIService()
videogen_service = VideoGenService()

@story_bp.route('/story/start', methods=['POST'])
def start_story_session():
    """
    Start a new story session when user says they're ready
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '').lower()
        
        # Check if user is ready to start
        if any(phrase in user_message for phrase in ['ready', 'start', 'begin', 'tell my story', 'i\'m ready']):
            session = story_service.create_new_session()
            first_question = story_service.get_next_question(session.session_id)
            
            return jsonify({
                'success': True,
                'session_id': session.session_id,
                'message': 'That\'s wonderful — thank you for being open and ready to share. 🌟\n\nThis process involves just four reflective questions, and I\'ll guide you through each one gently. Take your time with each response — depth and emotion are welcome here.\n\nLet\'s begin with the first question:',
                'question': first_question,
                'question_number': 1,
                'total_questions': 4,
                'session_complete': False
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Please let me know when you\'re ready to start telling your story! Just say something like "I\'m ready" or "Let\'s start".'
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@story_bp.route('/story/answer', methods=['POST'])
def submit_answer():
    """
    Submit an answer to a story question
    """
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        answer = data.get('answer')
        question_number = data.get('question_number')
        
        if not session_id or not answer:
            return jsonify({
                'success': False,
                'message': 'Session ID and answer are required'
            }), 400
        
        # Save the answer
        story_service.save_answer(session_id, question_number, answer)
        
        # Check if all questions are answered
        if question_number >= 4:
            # Generate story using OpenAI
            story_data = story_service.get_session_data(session_id)
            formatted_answers = story_service.get_all_answers_for_story_generation(session_id)
            generated_story = openai_service.generate_story_from_formatted_answers(formatted_answers)
            
            # Generate video from storyboard using VideoGen
            video_url = None
            try:
                video_url = openai_service.generate_video_from_storyboard(generated_story)
            except Exception as e:
                print(f"Video generation failed: {e}")
                video_url = None
            
            return jsonify({
                'success': True,
                'message': 'That\'s such a powerful takeaway — simple but truly life-changing. Sometimes it takes a sudden moment like that to remind us how fragile a second of distraction can be. Your story holds a quiet strength — a lesson in awareness, presence, and taking care of ourselves, even during everyday moments.\n\nNow that we have your four answers, I\'m going to turn them into a visual storyboard — something that could be used for a short video, animated clip, or even a slideshow. This will include suggested scenes, visuals, mood, and transitions to bring your experience to life with meaning and impact.',
                'storyboard': generated_story,
                'video_url': video_url,
                'session_complete': True,
                'question_number': question_number,
                'total_questions': 4
            })
        else:
            # Get next question
            next_question = story_service.get_next_question(session_id)
            
            # Provide contextual feedback based on the answer content
            feedback = story_service._generate_contextual_feedback(question_number, answer)
            
            return jsonify({
                'success': True,
                'message': f"{feedback}\n\nLet's continue with the next question:",
                'question': next_question,
                'question_number': question_number + 1,
                'total_questions': 4,
                'session_complete': False
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@story_bp.route('/story/current-question/<session_id>', methods=['GET'])
def get_current_question(session_id):
    """
    Get the current question for a session
    """
    try:
        current_question = story_service.get_next_question(session_id)
        session_data = story_service.get_session_data(session_id)
        
        if not session_data:
            return jsonify({
                'success': False,
                'message': 'Session not found'
            }), 404
        
        if not current_question:
            return jsonify({
                'success': True,
                'message': 'All questions have been answered',
                'session_complete': True,
                'question_number': len(session_data['answers']) + 1,
                'total_questions': 4
            })
        
        return jsonify({
            'success': True,
            'question': current_question,
            'question_number': session_data['current_question'],
            'total_questions': 4,
            'session_complete': False
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@story_bp.route('/story/session/<session_id>', methods=['GET'])
def get_session_status(session_id):
    """
    Get the current status of a story session
    """
    try:
        session_data = story_service.get_session_data(session_id)
        
        if not session_data:
            return jsonify({
                'success': False,
                'message': 'Session not found'
            }), 404
        
        return jsonify({
            'success': True,
            'session_data': session_data
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@story_bp.route('/video/generate', methods=['POST'])
def generate_video():
    """
    Generate a video from a text script using VideoGen API
    """
    try:
        data = request.get_json()
        script = data.get('script')
        
        if not script:
            return jsonify({
                'success': False,
                'message': 'Script is required'
            }), 400
        
        # Generate video using VideoGen
        video_url = openai_service.generate_video_from_script(script)
        
        return jsonify({
            'success': True,
            'video_url': video_url,
            'message': 'Video generated successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@story_bp.route('/video/generate-from-storyboard', methods=['POST'])
def generate_video_from_storyboard():
    """
    Generate a video from a storyboard using VideoGen API
    """
    try:
        data = request.get_json()
        storyboard = data.get('storyboard')
        
        if not storyboard:
            return jsonify({
                'success': False,
                'message': 'Storyboard is required'
            }), 400
        
        # Generate video using VideoGen
        video_url = openai_service.generate_video_from_storyboard(storyboard)
        
        return jsonify({
            'success': True,
            'video_url': video_url,
            'message': 'Video generated successfully from storyboard'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@story_bp.route('/video/status/<api_file_id>', methods=['GET'])
def get_video_status(api_file_id):
    """
    Get the status of a video generation using VideoGen API
    """
    try:
        if not api_file_id:
            return jsonify({
                'success': False,
                'message': 'API file ID is required'
            }), 400
        
        # Get video status from VideoGen
        result = videogen_service.get_video_file(api_file_id)
        
        return jsonify({
            'success': True,
            'result': result
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@story_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        'status': 'healthy',
        'message': 'Story Catcher Backend is running'
    })
