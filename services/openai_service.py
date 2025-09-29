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
                                "content": """You are a masterful visual storyteller. Create a storyboard based on the user's personal experience. Use ONLY their specific details. Format as:

**Storyboard: "[Title]" – [Subtitle]**

**Scene 1: "[Scene Name]"**
• **Visual**: [description]
• **Setting**: [description]
• **Mood**: [description]
• **Sound**: [description]
• **Transition**: [description]

Create 4-5 scenes total."""
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
            
            # Generate the storyboard using OpenAI
            print("Calling OpenAI API...")
            try:
                response = self._get_client().chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system",
                            "content": """You are a masterful visual storyteller and storyboard creator who specializes in transforming personal experiences into compelling visual narratives. 

CRITICAL INSTRUCTIONS:
1. You MUST use ONLY the specific details provided in the user's answers
2. Do NOT add generic content, scenarios, or unrelated content that the user didn't mention
3. Focus EXACTLY on what the person described in their responses
4. Use their exact words, locations, and experiences
5. Do NOT invent scenarios - stick to their actual story

FORMATTING REQUIREMENTS:
You MUST format your storyboard response EXACTLY as specified:
- **Storyboard: "[Title]" – [Subtitle]** header
- **Scene X: "[Scene Name]"** for each scene
- Bullet points (•) for each element (Visual, Setting/Action, Mood, Sound, Transition)
- Proper spacing and formatting
- 4-6 scenes total

Your expertise lies in:
1. **Accurate Storytelling**: Using ONLY the details from the user's answers
2. **Visual Storytelling**: Creating cinematic scenes based on their specific experience
3. **Emotional Resonance**: Capturing their actual emotional journey
4. **Scene Structure**: Breaking their story into meaningful scenes
5. **Authentic Details**: Using their specific locations, actions, and feelings

IMPORTANT: Follow the exact formatting template AND use only the details from their answers. Do not invent scenarios."""
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=1000,  # Reduced for faster response
                    temperature=0.8,
                    timeout=10  # Reduced timeout for Render worker limits
                )
                print("OpenAI API call completed successfully")
            except Exception as openai_error:
                print(f"OpenAI API call failed: {str(openai_error)}")
                print(f"Error type: {type(openai_error).__name__}")
                # Return a fallback storyboard if OpenAI fails
                return self._create_fallback_storyboard(formatted_answers)
            
            result = response.choices[0].message.content.strip()
            print(f"OpenAI response length: {len(result)} characters")
            return result
            
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
Based on the following personal interview responses, create a visual storyboard that brings this person's ACTUAL transformative experience to life:

{formatted_answers}

CRITICAL REQUIREMENTS:
- Use ONLY the specific details from their answers above
- Do NOT add generic scenarios or unrelated content that the user didn't mention
- Focus on their actual experience and story
- Use their exact locations, actions, and feelings
- Create scenes based on their real experience, not generic examples

**IMPORTANT FORMATTING REQUIREMENTS:**

Create a storyboard with this EXACT structure and formatting:

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

**Storyboard Guidelines:**
- Use bullet points (•) for each element
- Keep descriptions concise but vivid
- Focus on visual storytelling based on THEIR specific experience
- Include specific details from their story
- Create emotional resonance through mood and sound from their experience
- Make it suitable for video/animation production

**Requirements:**
- Create 4-6 scenes total
- Each scene should have Visual, Setting/Action, Mood, Sound, and Transition
- Use the person's specific experience details from their answers
- Make it visually compelling and emotionally resonant based on their real story
- Format exactly as shown above with proper spacing and bullet points
- DO NOT invent scenarios - use only what they described
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
                return "**Storyboard: \"Personal Journey\" – A Story of Growth**\n\n**Scene 1: \"The Moment\"**\n• **Visual**: A person in a meaningful moment of realization\n• **Setting**: A quiet, reflective environment\n• **Mood**: Contemplative and transformative\n• **Sound**: Gentle, ambient sounds\n• **Transition**: Fade to next scene\n\n**Scene 2: \"The Change\"**\n• **Visual**: The same person showing growth and understanding\n• **Action**: Moving forward with new perspective\n• **Mood**: Hopeful and determined\n• **Sound**: Uplifting, inspiring music\n• **Transition**: Smooth transition to conclusion\n\n**Scene 3: \"The Impact\"**\n• **Visual**: The person applying their new understanding\n• **Setting**: Daily life with positive changes\n• **Mood**: Peaceful and content\n• **Sound**: Warm, comforting tones\n• **Transition**: Fade to end"
            
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
            
            return f"""**Storyboard: "{title}" – A Journey of Growth**

**Scene 1: "The Beginning"**
• **Visual**: A person in their everyday environment
• **Setting**: The place where their story began
• **Mood**: Ordinary, perhaps unaware
• **Sound**: Ambient daily sounds
• **Transition**: Focus shifts to the moment

**Scene 2: "The Moment"**
• **Visual**: The pivotal moment of realization or change
• **Action**: The key action or decision that changed everything
• **Mood**: Intense, transformative
• **Sound**: Music that builds tension and release
• **Transition**: The aftermath begins

**Scene 3: "The Aftermath"**
• **Visual**: The person processing what happened
• **Setting**: A reflective space, perhaps alone
• **Mood**: Contemplative, processing
• **Sound**: Quieter, more introspective
• **Transition**: Moving toward understanding

**Scene 4: "The Change"**
• **Visual**: The person showing their transformation
• **Action**: Applying their new understanding
• **Mood**: Confident, peaceful, or determined
• **Sound**: Uplifting, hopeful music
• **Transition**: Integration into daily life

**Scene 5: "The New Normal"**
• **Visual**: The person in their transformed state
• **Setting**: Their daily life, but changed
• **Mood**: Content, aligned, at peace
• **Sound**: Warm, satisfying tones
• **Transition**: The story continues

**Scene 6: "The Impact"**
• **Visual**: How this change affects others around them
• **Action**: Sharing wisdom or living their values
• **Mood**: Inspiring, meaningful
• **Sound**: Full, rich, complete
• **Transition**: The journey continues"""
            
        except Exception as e:
            print(f"Error creating fallback storyboard: {e}")
            return "**Storyboard: \"Your Story\" – A Personal Journey**\n\n**Scene 1: \"The Beginning\"**\n• **Visual**: Your story begins here\n• **Setting**: The place where it all started\n• **Mood**: Setting the stage for transformation\n• **Sound**: The sounds of your experience\n• **Transition**: Moving toward the moment\n\n**Scene 2: \"The Moment\"**\n• **Visual**: The pivotal experience\n• **Action**: The key moment of change\n• **Mood**: The emotions of that time\n• **Sound**: The soundtrack of your story\n• **Transition**: Processing what happened\n\n**Scene 3: \"The Change\"**\n• **Visual**: How you transformed\n• **Setting**: Your new reality\n• **Mood**: The peace of understanding\n• **Sound**: Music of growth and wisdom\n• **Transition**: Living your new truth"
