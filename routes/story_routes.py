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
            print(f"Processing final answer for session {session_id}")
            # Generate story using OpenAI
            story_data = story_service.get_session_data(session_id)
            print(f"Session data retrieved: {story_data is not None}")
            formatted_answers = story_service.get_all_answers_for_story_generation(session_id)
            print(f"Formatted answers: {formatted_answers}")
            generated_story = openai_service.generate_story_from_formatted_answers(formatted_answers)
            print(f"Generated story response: {generated_story}")
            
            # Check if storyboard is still generating
            if generated_story == "STORYBOARD_GENERATING":
                return jsonify({
                    'success': True,
                    'message': 'That\'s such a powerful takeaway — simple but truly life-changing. Sometimes it takes a sudden moment like that to remind us how fragile a second of distraction can be. Your story holds a quiet strength — a lesson in awareness, presence, and taking care of ourselves, even during everyday moments.\n\nNow that we have your four answers, I\'m going to turn them into a visual storyboard — something that could be used for a short video, animated clip, or even a slideshow. This will include suggested scenes, visuals, mood, and transitions to bring your experience to life with meaning and impact.',
                    'storyboard': None,
                    'storyboard_generating': True,
                    'session_complete': True,
                    'question_number': question_number,
                    'total_questions': 4
                })
            else:
                # Store the generated storyboard in the session for later video generation
                story_service.save_generated_storyboard(session_id, generated_story)
                
                return jsonify({
                    'success': True,
                    'message': 'That\'s such a powerful takeaway — simple but truly life-changing. Sometimes it takes a sudden moment like that to remind us how fragile a second of distraction can be. Your story holds a quiet strength — a lesson in awareness, presence, and taking care of ourselves, even during everyday moments.\n\nNow that we have your four answers, I\'m going to turn them into a visual storyboard — something that could be used for a short video, animated clip, or even a slideshow. This will include suggested scenes, visuals, mood, and transitions to bring your experience to life with meaning and impact.',
                    'storyboard': generated_story,
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
        print(f"Error in submit_answer: {str(e)}")
        print(f"Session ID: {session_id}")
        print(f"Question Number: {question_number}")
        print(f"Answer: {answer}")
        import traceback
        traceback.print_exc()
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

@story_bp.route('/video/generate-from-session', methods=['POST'])
def generate_video_from_session():
    """
    Generate a video from a completed story session
    """
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        email = data.get('email', '')  # Optional email
        
        if not session_id:
            return jsonify({
                'success': False,
                'message': 'Session ID is required'
            }), 400
        
        # Get the stored storyboard from the session
        storyboard = story_service.get_generated_storyboard(session_id)
        if not storyboard:
            return jsonify({
                'success': False,
                'message': 'No storyboard found for this session'
            }), 404
        
        # Generate video from storyboard
        video_url = None
        try:
            print(f"Generating video for session {session_id}")
            video_url = openai_service.generate_video_from_storyboard(storyboard)
            print(f"Video generation initiated: {video_url}")
        except Exception as e:
            print(f"Video generation failed: {e}")
            import traceback
            traceback.print_exc()
            video_url = None
        
        # Store email and video info in session for later saving to Supabase
        if email:
            story_service.save_user_email(session_id, email)
        
        # Save to Supabase when video is ready
        if video_url and video_url.startswith('videogen://'):
            # Video is still processing, will save when ready
            pass
        elif video_url:
            # Video is ready, save to Supabase
            story_service.save_to_supabase(session_id, video_url)
        
        return jsonify({
            'success': True,
            'video_url': video_url,
            'message': 'Video generation started'
        })
    
    except Exception as e:
        print(f"Error in generate_video_from_session: {str(e)}")
        import traceback
        traceback.print_exc()
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
        email = data.get('email', '')  # Optional email
        session_id = data.get('session_id', '')  # Session ID
        
        if not storyboard:
            return jsonify({
                'success': False,
                'message': 'Storyboard is required'
            }), 400
        
        # Generate video using VideoGen
        video_url = openai_service.generate_video_from_storyboard(storyboard)
        
        # Store email temporarily in session (don't save to Supabase yet)
        if email and session_id:
            try:
                print(f"Storing email {email} temporarily for session {session_id}")
                story_service.save_user_email(session_id, email)
                
                # If video is ready (not videogen://), save to Supabase immediately
                if video_url and not video_url.startswith('videogen://'):
                    print(f"Saving video {video_url} and email to Supabase for session {session_id}")
                    story_service.save_to_supabase(session_id, video_url)
            except Exception as e:
                print(f"Failed to store email or save to Supabase: {e}")
        
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


@story_bp.route('/video/save-to-supabase', methods=['POST'])
def save_video_to_supabase():
    """
    Save final video URL to Supabase
    """
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        video_url = data.get('video_url')
        
        if not session_id or not video_url:
            return jsonify({
                'success': False,
                'message': 'Session ID and video URL are required'
            }), 400
        
        # Save to Supabase
        try:
            print(f"Saving final video {video_url} to Supabase for session {session_id}")
            success = story_service.save_to_supabase(session_id, video_url)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Video saved to Supabase successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to save video to Supabase'
                }), 500
                
        except Exception as e:
            print(f"Failed to save to Supabase: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@story_bp.route('/test-supabase', methods=['GET'])
def test_supabase():
    """
    Test Supabase connection and table access
    """
    try:
        import os
        from supabase import create_client
        
        # Get Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not supabase_url or not supabase_key:
            return jsonify({
                'success': False,
                'error': 'Supabase credentials not found',
                'url': supabase_url,
                'key': 'None' if not supabase_key else f'{supabase_key[:10]}...'
            }), 500
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Test table access
        response = supabase.table('story_submissions').select('*').limit(1).execute()
        
        return jsonify({
            'success': True,
            'message': 'Supabase connection successful',
            'table_accessible': True,
            'sample_data': response.data
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Supabase connection failed'
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

@story_bp.route('/storyboard/status/<session_id>', methods=['GET'])
def get_storyboard_status(session_id):
    """
    Get the status of storyboard generation for a session
    """
    try:
        status = openai_service.get_storyboard_status(session_id)
        
        if status['status'] == 'completed':
            # Store the completed storyboard in the session
            story_service.save_generated_storyboard(session_id, status['storyboard'])
        
        return jsonify({
            'success': True,
            'status': status['status'],
            'storyboard': status.get('storyboard'),
            'timestamp': status.get('timestamp')
        })
    
    except Exception as e:
        print(f"Error checking storyboard status: {str(e)}")
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
