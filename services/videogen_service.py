import requests
import time
import os
import re
from typing import Dict, Optional

class VideoGenService:
    def __init__(self):
        self.api_key = os.getenv('VIDEOGEN_API_KEY', 'b45efa105372a3880ddc2f18464437182597c666')
        self.base_url = 'https://ext.videogen.io/v1'
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def generate_video_from_script(self, script: str) -> str:
        """
        Generate a video from a text script using VideoGen API
        
        Args:
            script (str): The text script to convert to video
            
        Returns:
            str: The apiFileId for the generated video
        """
        try:
            url = f"{self.base_url}/script-to-video"
            
            # Truncate script to ensure max 1 minute duration (approximately 150 words)
            truncated_script = self._truncate_script_for_duration(script)
            
            payload = {
                "script": truncated_script,
                "aspectRatio": {
                    "width": 9,
                    "height": 16
                }
            }
            
            # VideoGen API supports aspectRatio parameter for vertical format
            # 9:16 aspect ratio creates vertical/portrait videos perfect for mobile
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            # Better error handling
            if response.status_code != 200:
                error_detail = response.text
                print(f"VideoGen API Error {response.status_code}: {error_detail}")
                raise Exception(f"VideoGen API request failed with status {response.status_code}: {error_detail}")
            
            response.raise_for_status()
            
            result = response.json()
            api_file_id = result.get('apiFileId')
            
            if not api_file_id:
                raise Exception("No apiFileId returned from VideoGen API")
            
            return api_file_id
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"VideoGen API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Video generation error: {str(e)}")
    
    def _truncate_script_for_duration(self, script: str, max_words: int = 150) -> str:
        """
        Truncate script to ensure video duration stays under 1 minute
        
        Args:
            script (str): The original script
            max_words (int): Maximum number of words (default: 150 for ~60 seconds)
            
        Returns:
            str: Truncated script
        """
        words = script.split()
        
        if len(words) <= max_words:
            return script
        
        # Truncate to max_words and ensure we end at a sentence
        truncated_words = words[:max_words]
        truncated_text = " ".join(truncated_words)
        
        # Find the last complete sentence
        last_period = truncated_text.rfind('.')
        if last_period > len(truncated_text) * 0.8:  # If we have a good sentence ending
            return truncated_text[:last_period + 1]
        
        # If no good sentence ending, add one
        return truncated_text + "."
    
    def get_video_file(self, api_file_id: str) -> Dict:
        """
        Get the video file information using the apiFileId
        
        Args:
            api_file_id (str): The apiFileId from the video generation
            
        Returns:
            Dict: Video file information including signed URL and status
        """
        try:
            url = f"{self.base_url}/get-file"
            params = {
                'apiFileId': api_file_id
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            return result
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"VideoGen API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Get video file error: {str(e)}")
    
    def wait_for_video_completion(self, api_file_id: str, max_wait_time: int = 300, poll_interval: int = 10) -> Dict:
        """
        Poll the VideoGen API until the video is ready
        
        Args:
            api_file_id (str): The apiFileId from the video generation
            max_wait_time (int): Maximum time to wait in seconds (default: 5 minutes)
            poll_interval (int): Time between polls in seconds (default: 10 seconds)
            
        Returns:
            Dict: Final video file information
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                result = self.get_video_file(api_file_id)
                loading_state = result.get('loadingState')
                
                if loading_state == 'FULFILLED':
                    return result
                elif loading_state == 'REJECTED':
                    raise Exception("Video generation was rejected")
                
                # Still processing, wait and try again
                time.sleep(poll_interval)
                
            except Exception as e:
                if "Failed to fetch video data" in str(e):
                    # Video might still be processing
                    time.sleep(poll_interval)
                    continue
                else:
                    raise e
        
        raise Exception(f"Video generation timed out after {max_wait_time} seconds")
    
    def generate_video_from_storyboard(self, storyboard: str) -> str:
        """
        Generate a video from a storyboard by converting it to a script
        
        Args:
            storyboard (str): The storyboard text
            
        Returns:
            str: The final video URL
        """
        try:
            # Convert storyboard to a script format suitable for VideoGen
            script = self._convert_storyboard_to_script(storyboard)
            
            # Generate video
            api_file_id = self.generate_video_from_script(script)
            
            # Wait for completion and get the final video URL
            result = self.wait_for_video_completion(api_file_id)
            
            return result.get('apiFileSignedUrl')
            
        except Exception as e:
            raise Exception(f"Storyboard to video generation error: {str(e)}")
    
    def _convert_storyboard_to_script(self, storyboard: str) -> str:
        """
        Convert a storyboard to a narrative script suitable for VideoGen voiceover
        
        Args:
            storyboard (str): The storyboard text
            
        Returns:
            str: A narrative script suitable for video voiceover
        """
        # Extract the main narrative from the storyboard
        lines = storyboard.split('\n')
        scenes = []
        
        # Extract title if present
        title = None
        for line in lines:
            if '**Storyboard:' in line and '**' in line:
                title = line.replace('**Storyboard:', '').replace('**', '').strip()
                break
        
        # Parse scenes
        current_scene = {}
        for line in lines:
            line = line.strip()
            
            # Scene header
            if line.startswith('**Scene') and ':' in line:
                if current_scene:  # Save previous scene
                    scenes.append(current_scene)
                
                # Extract scene name
                scene_name_match = re.search(r'(\d+): "([^"]+)"', line)
                if scene_name_match:
                    current_scene = {
                        'number': scene_name_match.group(1),
                        'name': scene_name_match.group(2),
                        'visual': '',
                        'setting': '',
                        'action': '',
                        'mood': ''
                    }
            
            # Extract scene details
            elif current_scene:
                if line.startswith('• **Visual**:'):
                    current_scene['visual'] = line.replace('• **Visual**:', '').strip()
                elif line.startswith('• **Setting**:'):
                    current_scene['setting'] = line.replace('• **Setting**:', '').strip()
                elif line.startswith('• **Action**:'):
                    current_scene['action'] = line.replace('• **Action**:', '').strip()
                elif line.startswith('• **Mood**:'):
                    current_scene['mood'] = line.replace('• **Mood**:', '').strip()
        
        # Add the last scene
        if current_scene:
            scenes.append(current_scene)
        
        # If no structured content found, create a simple narrative
        if not scenes:
            return self._create_simple_narrative(storyboard)
        
        # Create a flowing narrative script
        script_parts = []
        
        # Opening - keep it concise and first person
        if title:
            script_parts.append(f"This is my story of {title.lower()}.")
        else:
            script_parts.append("This is my personal story of transformation.")
        
        # Scene narratives - limit to 3-4 scenes for shorter video
        max_scenes = min(len(scenes), 4)  # Limit to 4 scenes max
        for i, scene in enumerate(scenes[:max_scenes]):
            scene_narrative = self._create_scene_narrative(scene, i + 1, max_scenes)
            script_parts.append(scene_narrative)
        
        # Closing - keep it brief and first person
        script_parts.append("This experience taught me that challenges can become opportunities for growth.")
        
        # Convert any remaining third person to first person
        final_script = self._convert_to_first_person("\n".join(script_parts))
        
        return final_script
    
    def _create_scene_narrative(self, scene: dict, scene_num: int, total_scenes: int) -> str:
        """Create a concise first-person narrative description for a single scene"""
        narrative_parts = []
        
        # Scene transition in first person - keep it brief
        if scene_num == 1:
            narrative_parts.append("I find myself")
        elif scene_num == total_scenes:
            narrative_parts.append("Finally")
        else:
            narrative_parts.append("Then")
        
        # Setting context - concise
        if scene.get('setting'):
            setting_desc = scene['setting'].lower()
            narrative_parts.append(f"{setting_desc}")
        
        # Visual description in first person - keep it short
        if scene.get('visual'):
            visual_desc = scene['visual']
            # Make it first person and concise
            if visual_desc.startswith('A '):
                visual_desc = f"I see {visual_desc[2:].lower()}"
            elif visual_desc.startswith('The '):
                visual_desc = f"I see {visual_desc[4:].lower()}"
            elif visual_desc.startswith('Close-up'):
                visual_desc = f"I notice {visual_desc.lower()}"
            else:
                visual_desc = f"I see {visual_desc.lower()}"
            
            narrative_parts.append(f"where {visual_desc}")
        
        # Action in first person - concise
        if scene.get('action'):
            action_desc = scene['action']
            if action_desc.startswith('I '):
                narrative_parts.append(f"Here, {action_desc.lower()}")
            else:
                narrative_parts.append(f"Here, I {action_desc.lower()}")
        
        # Mood - brief
        if scene.get('mood'):
            mood_desc = scene['mood']
            narrative_parts.append(f"feeling {mood_desc.lower()}")
        
        scene_text = ". ".join(narrative_parts) + "."
        
        # Ensure it's first person
        return self._convert_to_first_person(scene_text)
    
    def _convert_to_first_person(self, text: str) -> str:
        """Convert third person pronouns to first person"""
        # Common third person to first person conversions
        conversions = {
            'he ': 'I ',
            'she ': 'I ',
            'him ': 'me ',
            'her ': 'my ',
            'his ': 'my ',
            'himself': 'myself',
            'herself': 'myself',
            'the person': 'I',
            'the individual': 'I',
            'the protagonist': 'I',
            'the main character': 'I',
            'they ': 'I ',
            'them ': 'me ',
            'their ': 'my ',
            'themselves': 'myself',
            'He ': 'I ',
            'She ': 'I ',
            'Him ': 'Me ',
            'Her ': 'My ',
            'His ': 'My ',
            'Himself': 'Myself',
            'Herself': 'Myself',
            'They ': 'I ',
            'Them ': 'Me ',
            'Their ': 'My ',
            'Themselves': 'Myself',
        }
        
        # Apply conversions
        result = text
        for third_person, first_person in conversions.items():
            result = result.replace(third_person, first_person)
        
        # Fix common patterns
        result = re.sub(r'\bI I\b', 'I', result)  # Fix "I I" -> "I"
        result = re.sub(r'\bme me\b', 'me', result)  # Fix "me me" -> "me"
        result = re.sub(r'\bmy my\b', 'my', result)  # Fix "my my" -> "my"
        
        return result
    
    def _create_simple_narrative(self, storyboard: str) -> str:
        """Create a simple narrative from unstructured storyboard content"""
        # Extract key phrases and create a basic narrative
        lines = storyboard.split('\n')
        key_phrases = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('**') and not line.startswith('•'):
                # Clean up the line
                clean_line = re.sub(r'[^\w\s]', '', line)
                if len(clean_line.split()) > 3:  # Only meaningful phrases
                    key_phrases.append(clean_line)
        
        if key_phrases:
            narrative = "This is my personal story of transformation. " + " ".join(key_phrases[:3]) + ". "
            narrative += "It's my journey that shows how challenges can become opportunities for growth and understanding."
        else:
            narrative = "This is my personal story of transformation and growth. A journey that demonstrates the power of resilience and the importance of learning from my experiences."
        
        # Convert to first person
        return self._convert_to_first_person(narrative)
