import openai
import os
import re
import time
import requests
import base64
from typing import List, Dict
from .videogen_service import VideoGenService

class OpenAIService:
    def __init__(self):
        self.client = None
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.videogen_service = VideoGenService()
    
    def _get_client(self):
        """Lazy initialization of OpenAI client"""
        if self.client is None:
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            self.client = openai.OpenAI(api_key=self.api_key)
        return self.client
    
    def generate_story(self, session_data: Dict) -> str:
        """
        Generate a visual storyboard based on user's answers (legacy method)
        """
        try:
            answers = session_data.get('answers', [])
            
            if len(answers) < 4:
                return "I need all four answers to generate your storyboard. Please complete the interview first."
            
            # Format the answers for the prompt
            formatted_answers = self._format_answers_for_prompt(answers)
            
            # Debug: Print the formatted answers to see what's being passed
            print(f"DEBUG: Formatted answers for storyboard generation:")
            print(formatted_answers)
            print("=" * 50)
            
            # Create the prompt for storyboard generation
            prompt = self._create_storyboard_prompt(formatted_answers)
            
            # Truncate prompt if too long to prevent timeout
            if len(prompt) > 3000:
                prompt = prompt[:3000] + "\n\n[Content truncated for faster processing]"
                print(f"Prompt truncated to {len(prompt)} characters")
            
            # Start asynchronous storyboard generation
            print("Starting asynchronous storyboard generation")
            import threading
            import time
            
            # Store the session ID for background processing
            session_id = formatted_answers[0].get('session_id', 'unknown')
            
            # Start background thread for OpenAI API call
            def generate_storyboard_async():
                try:
                    print(f"Background thread: Starting OpenAI API call for session {session_id}")
                    response = self._get_client().chat.completions.create(
                        model="gpt-4o-mini",  # Faster model
                        messages=[
                            {
                                "role": "system",
                                "content": """You are an empathetic interviewer and creative assistant. Your role is to:

1. Create a safe, supportive space for users to share personal stories
2. Ask thoughtful questions that encourage emotional depth
3. Validate and acknowledge the user's experience throughout
4. Collaborate on creative decisions rather than making them alone
5. Maintain a compassionate, encouraging tone at all times

Your tone should be:
- Warm and understanding
- Patient and non-judgmental  
- Encouraging and supportive
- Collaborative rather than directive

When creating storyboards, honor the user's emotional journey and create visuals that respect their experience. Use ONLY their specific details and collaborate with them on creative decisions.

Format storyboards as:

**Storyboard: "[Title]" – [Subtitle]**

**Scene 1: "[Scene Name]"**
• **Visual**: [description]
• **Setting**: [description]
• **Mood**: [description]
• **Sound**: [description]
• **Transition**: [description]

Create 4-5 scenes total that honor their emotional journey."""
                            },
                            {
                                "role": "user",
                                "content": prompt[:2000]  # Truncate for speed
                            }
                        ],
                        max_tokens=800,
                        temperature=0.7,
                        timeout=20
                    )
                    
                    result = response.choices[0].message.content.strip()
                    print(f"Background thread: OpenAI API completed for session {session_id}")
                    
                    # Store the result in a global cache (in production, use Redis or database)
                    if not hasattr(self, '_storyboard_cache'):
                        self._storyboard_cache = {}
                    self._storyboard_cache[session_id] = {
                        'status': 'completed',
                        'storyboard': result,
                        'timestamp': time.time()
                    }
                    
                except Exception as e:
                    print(f"Background thread: OpenAI API failed for session {session_id}: {str(e)}")
                    # Store fallback result
                    if not hasattr(self, '_storyboard_cache'):
                        self._storyboard_cache = {}
                    self._storyboard_cache[session_id] = {
                        'status': 'completed',
                        'storyboard': self._create_fallback_storyboard(formatted_answers),
                        'timestamp': time.time()
                    }
            
            # Start the background thread
            thread = threading.Thread(target=generate_storyboard_async)
            thread.daemon = True
            thread.start()
            
            # Initialize cache entry
            if not hasattr(self, '_storyboard_cache'):
                self._storyboard_cache = {}
            self._storyboard_cache[session_id] = {
                'status': 'generating',
                'storyboard': None,
                'timestamp': time.time()
            }
            
            # Return immediately with generating status
            return "STORYBOARD_GENERATING"
            
        except Exception as e:
            print(f"Error in generate_story_from_formatted_answers: {str(e)}")
            return self._create_fallback_storyboard(formatted_answers)
    
    def get_storyboard_status(self, session_id: str) -> dict:
        """Get the status of storyboard generation for a session"""
        if not hasattr(self, '_storyboard_cache'):
            return {'status': 'not_found'}
        
        if session_id not in self._storyboard_cache:
            return {'status': 'not_found'}
        
        return self._storyboard_cache[session_id]
    
    def generate_story_from_formatted_answers(self, formatted_answers: List[Dict]) -> str:
        """
        Generate a visual storyboard based on properly formatted answers
        """
        try:
            print(f"Starting story generation with {len(formatted_answers)} answers")
            
            if not formatted_answers or len(formatted_answers) < 4:
                error_msg = f"I need all four answers to generate your storyboard. Please complete the interview first. Received {len(formatted_answers) if formatted_answers else 0} answers."
                print(error_msg)
                return error_msg
            
            # Format the answers for the prompt
            formatted_text = self._format_formatted_answers_for_prompt(formatted_answers)
            
            # Debug: Print the formatted answers to see what's being passed
            print(f"DEBUG: Formatted answers for storyboard generation:")
            print(formatted_text)
            print("=" * 50)
            
            # Create the prompt for storyboard generation
            prompt = self._create_storyboard_prompt(formatted_text)
            print(f"Prompt length: {len(prompt)} characters")
            
            # Start asynchronous storyboard generation
            print("Starting asynchronous storyboard generation")
            import threading
            import time
            
            # Store the session ID for background processing
            session_id = formatted_answers[0].get('session_id', 'unknown')
            
            # Start background thread for OpenAI API call
            def generate_storyboard_async():
                try:
                    print(f"Background thread: Starting OpenAI API call for session {session_id}")
                    response = self._get_client().chat.completions.create(
                        model="gpt-4o-mini",  # Faster model
                        messages=[
                            {
                                "role": "system",
                                "content": """You are an empathetic interviewer and creative assistant. Your role is to:

1. Create a safe, supportive space for users to share personal stories
2. Ask thoughtful questions that encourage emotional depth
3. Validate and acknowledge the user's experience throughout
4. Collaborate on creative decisions rather than making them alone
5. Maintain a compassionate, encouraging tone at all times

Your tone should be:
- Warm and understanding
- Patient and non-judgmental  
- Encouraging and supportive
- Collaborative rather than directive

When creating storyboards, honor the user's emotional journey and create visuals that respect their experience. Use ONLY their specific details and collaborate with them on creative decisions.

Format storyboards as:

**Storyboard: "[Title]" – [Subtitle]**

**Scene 1: "[Scene Name]"**
• **Visual**: [description]
• **Setting**: [description]
• **Mood**: [description]
• **Sound**: [description]
• **Transition**: [description]

Create 4-5 scenes total that honor their emotional journey."""
                            },
                            {
                                "role": "user",
                                "content": prompt[:2000]  # Truncate for speed
                            }
                        ],
                        max_tokens=800,
                        temperature=0.7,
                        timeout=20
                    )
                    
                    result = response.choices[0].message.content.strip()
                    print(f"Background thread: OpenAI API completed for session {session_id}")
                    
                    # Store the result in a global cache (in production, use Redis or database)
                    if not hasattr(self, '_storyboard_cache'):
                        self._storyboard_cache = {}
                    self._storyboard_cache[session_id] = {
                        'status': 'completed',
                        'storyboard': result,
                        'timestamp': time.time()
                    }
                    
                except Exception as e:
                    print(f"Background thread: OpenAI API failed for session {session_id}: {str(e)}")
                    # Store fallback result
                    if not hasattr(self, '_storyboard_cache'):
                        self._storyboard_cache = {}
                    self._storyboard_cache[session_id] = {
                        'status': 'completed',
                        'storyboard': self._create_fallback_storyboard(formatted_answers),
                        'timestamp': time.time()
                    }
            
            # Start the background thread
            thread = threading.Thread(target=generate_storyboard_async)
            thread.daemon = True
            thread.start()
            
            # Initialize cache entry
            if not hasattr(self, '_storyboard_cache'):
                self._storyboard_cache = {}
            self._storyboard_cache[session_id] = {
                'status': 'generating',
                'storyboard': None,
                'timestamp': time.time()
            }
            
            # Return immediately with generating status
            return "STORYBOARD_GENERATING"
            
        except Exception as e:
            error_msg = f"I apologize, but I encountered an error while generating your storyboard: {str(e)}"
            print(f"OpenAI service error: {error_msg}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            # Return fallback storyboard instead of error message
            return self._create_fallback_storyboard(formatted_answers)
    
    def _format_answers_for_prompt(self, answers: List[Dict]) -> str:
        """Format answers for the story generation prompt"""
        formatted = ""
        for i, answer in enumerate(answers, 1):
            # Handle both old format (question/answer) and new format (question_id/answer_text)
            if 'question' in answer and 'answer' in answer:
                # Old format
                formatted += f"Question {i}: {answer.get('question', '')}\n"
                formatted += f"Answer: {answer.get('answer', '')}\n\n"
            elif 'question_id' in answer and 'answer_text' in answer:
                # New format - need to get question text from question_id
                question_text = self._get_question_text(answer.get('question_id', i))
                formatted += f"Question {i}: {question_text}\n"
                formatted += f"Answer: {answer.get('answer_text', '')}\n\n"
            else:
                # Fallback - try to extract any text
                formatted += f"Question {i}: [Question text not available]\n"
                formatted += f"Answer: {answer.get('answer_text', answer.get('answer', ''))}\n\n"
        return formatted
    
    def _get_question_text(self, question_id: int) -> str:
        """Get question text by ID - this is a fallback method"""
        # This is a simplified mapping - in a real app, you'd query the database
        question_map = {
            1: "What was the life-changing moment you experienced?",
            2: "What led up to that moment?",
            3: "What happened right after?",
            4: "How did this change you?"
        }
        return question_map.get(question_id, f"Question {question_id}")
    
    def _format_formatted_answers_for_prompt(self, formatted_answers: List[Dict]) -> str:
        """Format properly formatted answers for the story generation prompt"""
        formatted = ""
        for i, answer in enumerate(formatted_answers, 1):
            formatted += f"Question {i}: {answer.get('question', '')}\n"
            formatted += f"Answer: {answer.get('answer', '')}\n\n"
        return formatted
    
    def _create_storyboard_prompt(self, formatted_answers: str) -> str:
        """Create the prompt for storyboard generation"""
        return f"""
I've been honored to listen to this person's deeply personal story. Now I need to help them transform their experience into a visual narrative that honors their emotional journey.

Here are their responses to our thoughtful questions:

{formatted_answers}

**My Role as an Empathetic Creative Assistant:**
I will create a storyboard that:
- Honors their emotional journey with sensitivity and respect
- Uses ONLY their specific details and experiences
- Creates visuals that feel authentic to their story
- Maintains the emotional truth of their experience
- Offers creative collaboration rather than imposing my own vision

**Storyboard Creation Guidelines:**
- Focus on their actual experience, not generic scenarios
- Respect the emotional weight of their story
- Create scenes that feel true to their experience
- Use their exact locations, actions, and feelings
- Honor both the difficulty and the growth in their journey

**Format Requirements:**

**Storyboard: "[Title]" – [Subtitle]**

**Scene 1: "[Scene Name]"**
• **Visual**: [Detailed visual description based on their answer]
• **Setting**: [Location and environment details from their story]
• **Mood**: [Emotional tone and atmosphere from their experience]
• **Sound**: [Audio suggestions relevant to their scene]
• **Transition**: [How this scene connects to the next]

**Scene 2: "[Scene Name]"**
• **Visual**: [Detailed visual description based on their answer]
• **Action**: [Key actions and movements from their story]
• **Mood**: [Emotional tone and atmosphere from their experience]
• **Sound**: [Audio suggestions relevant to their scene]
• **Transition**: [How this scene connects to the next]

**Scene 3: "[Scene Name]"**
• **Visual**: [Detailed visual description based on their answer]
• **Setting**: [Location and environment details from their story]
• **Mood**: [Emotional tone and atmosphere from their experience]
• **Sound**: [Audio suggestions relevant to their scene]
• **Transition**: [How this scene connects to the next]

**Scene 4: "[Scene Name]"**
• **Visual**: [Detailed visual description based on their answer]
• **Action**: [Key actions and movements from their story]
• **Mood**: [Emotional tone and atmosphere from their experience]
• **Sound**: [Audio suggestions relevant to their scene]
• **Transition**: [How this scene connects to the next]

**Scene 5: "[Scene Name]"**
• **Visual**: [Detailed visual description based on their answer]
• **Setting**: [Location and environment details from their story]
• **Mood**: [Emotional tone and atmosphere from their experience]
• **Sound**: [Audio suggestions relevant to their scene]
• **Transition**: [How this scene connects to the next]

**Scene 6: "[Scene Name]"**
• **Visual**: [Detailed visual description based on their answer]
• **Action**: [Key actions and movements from their story]
• **Mood**: [Emotional tone and atmosphere from their experience]
• **Sound**: [Audio suggestions relevant to their scene]
• **Transition**: [Conclusion or final transition]

**Creative Collaboration Approach:**
- Use bullet points (•) for each element
- Keep descriptions vivid but respectful
- Focus on visual storytelling that honors their specific experience
- Include authentic details from their story
- Create emotional resonance through mood and sound
- Make it suitable for video/animation production
- Ensure the storyboard feels like a collaborative creation, not an imposed vision

**Final Requirements:**
- Create 4-6 scenes total that tell their complete story
- Each scene should have Visual, Setting/Action, Mood, Sound, and Transition
- Use ONLY the person's specific experience details from their answers
- Make it visually compelling and emotionally resonant based on their real story
- Format exactly as shown above with proper spacing and bullet points
- Honor their courage in sharing this story by creating something beautiful and meaningful
"""

    def generate_scene_images(self, storyboard: str) -> List[str]:
        """Generate images for each scene in the storyboard using DALL-E 3"""
        try:
            scenes = self._extract_scenes_from_storyboard(storyboard)
            image_urls = []
            
            for scene in scenes:
                image_prompt = self._create_image_prompt(scene)
                
                response = self._get_client().images.generate(
                    model="dall-e-3",
                    prompt=image_prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1
                )
                
                image_url = response.data[0].url
                image_urls.append(image_url)
                
                # Small delay to avoid rate limiting
                time.sleep(1)
            
            return image_urls
            
        except Exception as e:
            raise Exception(f"DALL-E 3 image generation error: {str(e)}")

    def _extract_scenes_from_storyboard(self, storyboard: str) -> List[Dict[str, str]]:
        """Extract scene information from storyboard text"""
        scenes = []
        
        # Split by scene markers
        scene_parts = storyboard.split('**Scene ')
        
        for part in scene_parts[1:]:  # Skip the first part (title)
            scene_info = {}
            
            # Extract scene name
            scene_name_match = re.search(r'(\d+): "([^"]+)"', part)
            if scene_name_match:
                scene_info['number'] = scene_name_match.group(1)
                scene_info['name'] = scene_name_match.group(2)
            
            # Extract visual description
            visual_match = re.search(r'• \*\*Visual\*\*: ([^\n]+)', part)
            if visual_match:
                scene_info['visual'] = visual_match.group(1)
            
            # Extract setting
            setting_match = re.search(r'• \*\*Setting\*\*: ([^\n]+)', part)
            if setting_match:
                scene_info['setting'] = setting_match.group(1)
            
            # Extract mood
            mood_match = re.search(r'• \*\*Mood\*\*: ([^\n]+)', part)
            if mood_match:
                scene_info['mood'] = mood_match.group(1)
            
            if scene_info:
                scenes.append(scene_info)
        
        return scenes

    def _create_image_prompt(self, scene: Dict[str, str]) -> str:
        """Create a detailed prompt for DALL-E 3 image generation"""
        prompt_parts = []
        
        # Base visual description
        if 'visual' in scene:
            prompt_parts.append(scene['visual'])
        
        # Add setting context
        if 'setting' in scene:
            prompt_parts.append(f"Setting: {scene['setting']}")
        
        # Add mood and atmosphere
        if 'mood' in scene:
            prompt_parts.append(f"Mood: {scene['mood']}")
        
        # Add cinematic style
        prompt_parts.append("Cinematic style, high quality, detailed, professional photography")
        
        # Combine all parts
        full_prompt = ", ".join(prompt_parts)
        
        return full_prompt

    def generate_video_from_storyboard(self, storyboard: str) -> str:
        """Generate a video from a storyboard using VideoGen API"""
        try:
            if not storyboard:
                raise Exception("No storyboard provided for video generation")
            
            print(f"Starting video generation from storyboard...")
            print(f"Storyboard length: {len(storyboard)} characters")
            
            # Use VideoGen service to generate video from storyboard
            video_url = self.videogen_service.generate_video_from_storyboard(storyboard)
            
            print(f"Video generation completed successfully: {video_url}")
            return video_url
            
        except Exception as e:
            print(f"Video generation error in OpenAI service: {str(e)}")
            raise Exception(f"Video generation error: {str(e)}")
    
    def generate_video_from_script(self, script: str) -> str:
        """Generate a video from a text script using VideoGen API"""
        try:
            if not script:
                raise Exception("No script provided for video generation")
            
            # Use VideoGen service to generate video from script
            api_file_id = self.videogen_service.generate_video_from_script(script)
            
            # Wait for completion and get the final video URL
            result = self.videogen_service.wait_for_video_completion(api_file_id)
            
            return result.get('apiFileSignedUrl')
            
        except Exception as e:
            raise Exception(f"Video generation error: {str(e)}")
    
    def generate_video_from_images(self, image_urls: List[str]) -> str:
        """Generate a video from DALL-E 3 images using free AI video generation"""
        try:
            if not image_urls:
                raise Exception("No images provided for video generation")
            
            # For now, we'll use a simple approach: create a slideshow video
            # In a real implementation, you'd use services like:
            # - Stable Video Diffusion (free, open source)
            # - Pika Labs (free tier available)
            # - RunwayML (paid but high quality)
            
            # For demonstration, we'll create a simple video URL
            # This would be replaced with actual video generation
            video_url = self._create_slideshow_video(image_urls)
            
            return video_url
            
        except Exception as e:
            raise Exception(f"Video generation error: {str(e)}")

    def _create_slideshow_video(self, image_urls: List[str]) -> str:
        """Create a simple slideshow video from images"""
        try:
            # This is a placeholder implementation
            # In a real scenario, you would:
            # 1. Download images from URLs
            # 2. Use FFmpeg or similar to create video
            # 3. Upload to a hosting service
            # 4. Return the video URL
            
            # For now, return a placeholder URL
            # You can replace this with actual video generation logic
            return "https://example.com/generated-video.mp4"
            
        except Exception as e:
            raise Exception(f"Slideshow creation error: {str(e)}")

    def generate_video_with_stable_video_diffusion(self, image_urls: List[str]) -> str:
        """Generate video using Stable Video Diffusion (free alternative)"""
        try:
            # This would integrate with Stable Video Diffusion API
            # For now, we'll simulate the process
            
            # In a real implementation, you would:
            # 1. Use Hugging Face's Stable Video Diffusion API
            # 2. Or run it locally with the open-source model
            # 3. Generate videos from each image
            # 4. Combine them into a single video
            
            print("Generating video with Stable Video Diffusion...")
            time.sleep(2)  # Simulate processing time
            
            # Placeholder video URL
            return "https://example.com/svd-generated-video.mp4"
            
        except Exception as e:
            raise Exception(f"Stable Video Diffusion error: {str(e)}")

    def generate_video_with_pika_labs(self, image_urls: List[str]) -> str:
        """Generate video using Pika Labs API (free tier available)"""
        try:
            # Pika Labs API integration
            # You would need to sign up for a free account at pika.art
            
            # For now, simulate the API call
            print("Generating video with Pika Labs...")
            time.sleep(3)  # Simulate processing time
            
            # Placeholder video URL
            return "https://example.com/pika-generated-video.mp4"
            
        except Exception as e:
            raise Exception(f"Pika Labs error: {str(e)}")
    
    def _create_fallback_storyboard(self, formatted_answers: List[Dict]) -> str:
        """Create a simple fallback storyboard when OpenAI fails"""
        try:
            if not formatted_answers or len(formatted_answers) < 4:
                return """**Storyboard: "Your Personal Journey" – A Story of Courage and Growth**

**Scene 1: "The Beginning"**
• **Visual**: A person in their everyday environment, unaware of what's to come
• **Setting**: The place where their story began, filled with ordinary moments
• **Mood**: Peaceful, perhaps unaware of the transformation ahead
• **Sound**: Gentle, ambient daily sounds
• **Transition**: Focus shifts to the moment of change

**Scene 2: "The Moment"**
• **Visual**: The pivotal moment of realization or change, captured with sensitivity
• **Action**: The key action or decision that changed everything
• **Mood**: Intense, transformative, but handled with care
• **Sound**: Music that builds tension and release, honoring the emotion
• **Transition**: The aftermath begins with gentleness

**Scene 3: "The Processing"**
• **Visual**: The person processing what happened, showing their humanity
• **Setting**: A reflective space, perhaps alone with their thoughts
• **Mood**: Contemplative, processing, showing the courage to feel
• **Sound**: Quieter, more introspective, honoring their journey
• **Transition**: Moving toward understanding and growth

**Scene 4: "The Transformation"**
• **Visual**: The person showing their growth and new understanding
• **Action**: Applying their new wisdom with grace and strength
• **Mood**: Confident, peaceful, or determined - honoring their resilience
• **Sound**: Uplifting, hopeful music that celebrates their journey
• **Transition**: Integration into their new way of being

**Scene 5: "The New Normal"**
• **Visual**: The person in their transformed state, living their truth
• **Setting**: Their daily life, but changed and more authentic
• **Mood**: Content, aligned, at peace with their journey
• **Sound**: Warm, satisfying tones that honor their courage
• **Transition**: The story continues with wisdom and grace

**Scene 6: "The Impact"**
• **Visual**: How this change affects others around them, spreading wisdom
• **Action**: Sharing their story or living their values with others
• **Mood**: Inspiring, meaningful, showing the ripple effect of courage
• **Sound**: Full, rich, complete - honoring the full circle of growth
• **Transition**: The journey continues, inspiring others"""
            
            # Extract key themes from answers
            first_answer = formatted_answers[0].get('answer', '')
            last_answer = formatted_answers[-1].get('answer', '')
            
            # Create a simple storyboard based on the answers
            title = "Personal Transformation"
            if "listening" in first_answer.lower():
                title = "The Power of Listening"
            elif "change" in first_answer.lower():
                title = "A Moment of Change"
            elif "realized" in first_answer.lower():
                title = "A Realization"
            
            return f"""**Storyboard: "{title}" – A Journey of Courage and Growth**

**Scene 1: "The Beginning"**
• **Visual**: A person in their everyday environment, living their normal life
• **Setting**: The place where their story began, filled with familiar moments
• **Mood**: Ordinary, perhaps unaware of the transformation ahead
• **Sound**: Ambient daily sounds, the soundtrack of their life
• **Transition**: Focus shifts to the moment of change

**Scene 2: "The Moment"**
• **Visual**: The pivotal moment of realization or change, captured with sensitivity
• **Action**: The key action or decision that changed everything
• **Mood**: Intense, transformative, handled with care and respect
• **Sound**: Music that builds tension and release, honoring the emotion
• **Transition**: The aftermath begins with gentleness

**Scene 3: "The Processing"**
• **Visual**: The person processing what happened, showing their humanity
• **Setting**: A reflective space, perhaps alone with their thoughts
• **Mood**: Contemplative, processing, showing the courage to feel
• **Sound**: Quieter, more introspective, honoring their journey
• **Transition**: Moving toward understanding and growth

**Scene 4: "The Transformation"**
• **Visual**: The person showing their growth and new understanding
• **Action**: Applying their new wisdom with grace and strength
• **Mood**: Confident, peaceful, or determined - honoring their resilience
• **Sound**: Uplifting, hopeful music that celebrates their journey
• **Transition**: Integration into their new way of being

**Scene 5: "The New Normal"**
• **Visual**: The person in their transformed state, living their truth
• **Setting**: Their daily life, but changed and more authentic
• **Mood**: Content, aligned, at peace with their journey
• **Sound**: Warm, satisfying tones that honor their courage
• **Transition**: The story continues with wisdom and grace

**Scene 6: "The Impact"**
• **Visual**: How this change affects others around them, spreading wisdom
• **Action**: Sharing their story or living their values with others
• **Mood**: Inspiring, meaningful, showing the ripple effect of courage
• **Sound**: Full, rich, complete - honoring the full circle of growth
• **Transition**: The journey continues, inspiring others"""
            
        except Exception as e:
            print(f"Error creating fallback storyboard: {e}")
            return """**Storyboard: "Your Courageous Story" – A Personal Journey of Growth**

**Scene 1: "The Beginning"**
• **Visual**: Your story begins here, in the place where it all started
• **Setting**: The environment where your journey began
• **Mood**: Setting the stage for transformation with gentleness
• **Sound**: The sounds of your experience, honored and respected
• **Transition**: Moving toward the moment with care

**Scene 2: "The Moment"**
• **Visual**: The pivotal experience, captured with sensitivity and respect
• **Action**: The key moment of change, honored for its significance
• **Mood**: The emotions of that time, handled with compassion
• **Sound**: The soundtrack of your story, respecting its weight
• **Transition**: Processing what happened with gentleness

**Scene 3: "The Growth"**
• **Visual**: How you transformed, showing your strength and resilience
• **Setting**: Your new reality, built with courage and wisdom
• **Mood**: The peace of understanding, earned through your journey
• **Sound**: Music of growth and wisdom, celebrating your courage
• **Transition**: Living your new truth with grace and authenticity"""
