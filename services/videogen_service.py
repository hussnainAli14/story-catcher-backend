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
            
            print(f"VideoGen API Key: {self.api_key[:10]}..." if self.api_key else "No API key")
            print(f"Script length: {len(truncated_script)} characters")
            print(f"Truncated script preview: {truncated_script[:100]}...")
            
            payload = {
                "script": truncated_script,
                "aspectRatio": {
                    "width": 9,
                    "height": 16
                }
            }
            
            print(f"Sending request to VideoGen API: {url}")
            print(f"Payload: {payload}")
            
            # Reduce timeout to prevent worker crashes
            response = requests.post(url, headers=self.headers, json=payload, timeout=15)
            
            print(f"VideoGen API Response Status: {response.status_code}")
            print(f"VideoGen API Response Headers: {dict(response.headers)}")
            
            # Better error handling
            if response.status_code != 200:
                error_detail = response.text
                print(f"VideoGen API Error {response.status_code}: {error_detail}")
                raise Exception(f"VideoGen API request failed with status {response.status_code}: {error_detail}")
            
            response.raise_for_status()
            
            result = response.json()
            print(f"VideoGen API Response: {result}")
            
            api_file_id = result.get('apiFileId')
            
            if not api_file_id:
                raise Exception("No apiFileId returned from VideoGen API")
            
            return api_file_id
            
        except requests.exceptions.Timeout:
            print("VideoGen API request timed out")
            raise Exception("Video generation request timed out")
        except requests.exceptions.RequestException as e:
            print(f"Request exception: {str(e)}")
            raise Exception(f"VideoGen API request failed: {str(e)}")
        except Exception as e:
            print(f"General exception: {str(e)}")
            raise Exception(f"Video generation error: {str(e)}")
    
    def _truncate_script_for_duration(self, script: str, max_words: int = 150) -> str:
        """
        Intelligently truncate script to ensure video duration stays under 1 minute
        while preserving the complete story arc
        
        Args:
            script (str): The original script
            max_words (int): Maximum number of words (default: 150 for ~60 seconds)
            
        Returns:
            str: Truncated script that maintains story completeness
        """
        words = script.split()
        
        if len(words) <= max_words:
            return script
        
        # Split script into sentences to preserve story structure
        sentences = script.split('. ')
        
        # Try to include complete sentences up to word limit
        included_sentences = []
        word_count = 0
        
        for sentence in sentences:
            sentence_words = sentence.split()
            # Add 1 for the period that was removed in split
            sentence_word_count = len(sentence_words) + 1
            
            if word_count + sentence_word_count <= max_words:
                included_sentences.append(sentence)
                word_count += sentence_word_count
            else:
                # If adding this sentence would exceed limit, check if we can fit a partial
                remaining_words = max_words - word_count
                if remaining_words >= 10:  # Only if we have enough words for meaningful content
                    # Try to include a meaningful portion of the sentence
                    partial_sentence = ' '.join(sentence_words[:remaining_words])
                    if partial_sentence.strip():
                        included_sentences.append(partial_sentence)
                break
        
        # Join sentences and ensure proper ending
        if included_sentences:
            truncated_text = '. '.join(included_sentences)
            # Ensure it ends with a period
            if not truncated_text.endswith('.'):
                truncated_text += '.'
            return truncated_text
        
        # Fallback: simple word truncation
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
        poll_count = 0
        
        while time.time() - start_time < max_wait_time:
            try:
                poll_count += 1
                print(f"Polling video status (attempt {poll_count}) for {api_file_id}")
                
                result = self.get_video_file(api_file_id)
                loading_state = result.get('loadingState')
                
                print(f"Video status: {loading_state}")
                
                if loading_state == 'FULFILLED':
                    print(f"Video completed successfully: {result}")
                    return result
                elif loading_state == 'REJECTED':
                    raise Exception("Video generation was rejected")
                
                # Still processing, wait and try again
                print(f"Video still processing, waiting {poll_interval} seconds...")
                time.sleep(poll_interval)
                
            except Exception as e:
                print(f"Polling error (attempt {poll_count}): {str(e)}")
                if "Failed to fetch video data" in str(e) or "404" in str(e):
                    # Video might still be processing or API might be slow
                    print(f"Video might still be processing, waiting {poll_interval} seconds...")
                    time.sleep(poll_interval)
                    continue
                else:
                    # For other errors, don't fail immediately, try a few more times
                    if poll_count >= 3:
                        raise e
                    time.sleep(poll_interval)
                    continue
        
        raise Exception(f"Video generation timed out after {max_wait_time} seconds")
    
    def generate_video_from_storyboard(self, storyboard: str) -> str:
        """
        Generate a video from a storyboard by converting it to a script
        
        Args:
            storyboard (str): The storyboard text
            
        Returns:
            str: The final video URL or apiFileId for later retrieval
        """
        try:
            print(f"Converting storyboard to script...")
            # Convert storyboard to a script format suitable for VideoGen
            script = self._convert_storyboard_to_script(storyboard)
            print(f"Script conversion complete, length: {len(script)}")
            
            # Generate video
            print(f"Starting video generation...")
            api_file_id = self.generate_video_from_script(script)
            print(f"Video generation initiated, apiFileId: {api_file_id}")
            
            # Return the apiFileId immediately to prevent timeout
            # The frontend will poll for completion
            return f"videogen://{api_file_id}"
            
        except Exception as e:
            print(f"Storyboard to video generation error: {str(e)}")
            raise Exception(f"Storyboard to video generation error: {str(e)}")
    
    def _convert_storyboard_to_script(self, storyboard: str) -> str:
        """
        Convert a storyboard to a narrative script suitable for VideoGen voiceover
        
        Args:
            storyboard (str): The storyboard text
            
        Returns:
            str: A narrative script suitable for video voiceover (optimized for 1-minute duration)
        """
        # Extract the main narrative from the storyboard
        lines = storyboard.split('\n')
        scenes = []
        
        # Extract title if present - with better cleaning
        title = None
        for line in lines:
            if '**Storyboard:' in line and '**' in line:
                # Extract title with better cleaning
                title_raw = line.replace('**Storyboard:', '').replace('**', '').strip()
                # Clean the title by removing special characters and formatting
                title = self._clean_title_for_voiceover(title_raw)
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
        
        # Create a complete narrative that fits within 1-minute constraint
        return self._create_complete_narrative(scenes, title)
    
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
        
        # Setting context - concise and clean
        if scene.get('setting'):
            setting_desc = self._clean_text_for_voiceover(scene['setting'].lower())
            if setting_desc:
                narrative_parts.append(setting_desc)
        
        # Visual description in first person - keep it short and clean
        if scene.get('visual'):
            visual_desc = self._clean_text_for_voiceover(scene['visual'])
            if visual_desc:
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
        
        # Action in first person - concise and clean
        if scene.get('action'):
            action_desc = self._clean_text_for_voiceover(scene['action'])
            if action_desc:
                if action_desc.startswith('I '):
                    narrative_parts.append(f"Here, {action_desc.lower()}")
                else:
                    narrative_parts.append(f"Here, I {action_desc.lower()}")
        
        # Mood - brief and clean
        if scene.get('mood'):
            mood_desc = self._clean_text_for_voiceover(scene['mood'])
            if mood_desc:
                narrative_parts.append(f"feeling {mood_desc.lower()}")
        
        # Join parts and ensure clean output
        scene_text = ". ".join(narrative_parts) + "."
        
        # Clean the final text and ensure it's first person
        final_text = self._convert_to_first_person(scene_text)
        return self._clean_text_for_voiceover(final_text)
    
    def _create_complete_narrative(self, scenes: list, title: str) -> str:
        """
        Create a complete narrative that tells the full story within 1-minute constraint
        
        Args:
            scenes (list): List of scene dictionaries
            title (str): Story title (cleaned)
            
        Returns:
            str: Complete narrative script optimized for 1-minute duration
        """
        # Target word count for 1-minute video (approximately 150-180 words)
        target_words = 160
        
        # Create different narrative strategies based on number of scenes
        if len(scenes) <= 3:
            # Few scenes - can include more detail per scene
            return self._create_detailed_narrative(scenes, title, target_words)
        elif len(scenes) <= 6:
            # Medium number of scenes - balanced approach
            return self._create_balanced_narrative(scenes, title, target_words)
        else:
            # Many scenes - focus on key story beats
            return self._create_summary_narrative(scenes, title, target_words)
    
    def _create_detailed_narrative(self, scenes: list, title: str, target_words: int) -> str:
        """Create detailed narrative for stories with few scenes"""
        script_parts = []
        
        # Opening
        if title and len(title.strip()) > 0:
            script_parts.append(f"This is my story of {title.lower()}.")
        else:
            script_parts.append("This is my personal story of transformation.")
        
        # Include all scenes with more detail
        for i, scene in enumerate(scenes):
            scene_narrative = self._create_scene_narrative(scene, i + 1, len(scenes))
            script_parts.append(scene_narrative)
        
        # Closing
        script_parts.append("This experience taught me that challenges can become opportunities for growth.")
        
        # Join and clean
        final_script = self._convert_to_first_person("\n".join(script_parts))
        # Don't over-clean the final script - just basic cleanup
        final_script = self._basic_clean_text(final_script)
        
        # Check word count and adjust if needed
        word_count = len(final_script.split())
        if word_count > target_words:
            return self._truncate_script_for_duration(final_script, target_words)
        
        return final_script
    
    def _create_balanced_narrative(self, scenes: list, title: str, target_words: int) -> str:
        """Create balanced narrative for stories with medium number of scenes"""
        script_parts = []
        
        # Opening
        if title and len(title.strip()) > 0:
            script_parts.append(f"This is my story of {title.lower()}.")
        else:
            script_parts.append("This is my personal story of transformation.")
        
        # Select key scenes to tell complete story
        key_scenes = self._select_key_scenes(scenes)
        
        for i, scene in enumerate(key_scenes):
            scene_narrative = self._create_scene_narrative(scene, i + 1, len(key_scenes))
            script_parts.append(scene_narrative)
        
        # Closing
        script_parts.append("This experience taught me that challenges can become opportunities for growth.")
        
        # Join and clean
        final_script = self._convert_to_first_person("\n".join(script_parts))
        # Don't over-clean the final script - just basic cleanup
        final_script = self._basic_clean_text(final_script)
        
        # Check word count and adjust if needed
        word_count = len(final_script.split())
        if word_count > target_words:
            return self._truncate_script_for_duration(final_script, target_words)
        
        return final_script
    
    def _create_summary_narrative(self, scenes: list, title: str, target_words: int) -> str:
        """Create summary narrative for stories with many scenes"""
        script_parts = []
        
        # Opening
        if title and len(title.strip()) > 0:
            script_parts.append(f"This is my story of {title.lower()}.")
        else:
            script_parts.append("This is my personal story of transformation.")
        
        # Create a summary that covers the complete story arc
        beginning_scenes = scenes[:2] if len(scenes) >= 2 else scenes[:1]
        middle_scenes = scenes[len(scenes)//2-1:len(scenes)//2+1] if len(scenes) >= 4 else scenes[1:2]
        ending_scenes = scenes[-2:] if len(scenes) >= 2 else scenes[-1:]
        
        # Combine key scenes
        key_scenes = beginning_scenes + middle_scenes + ending_scenes
        # Remove duplicates while preserving order
        seen = set()
        unique_scenes = []
        for scene in key_scenes:
            scene_id = scene.get('number', '')
            if scene_id not in seen:
                seen.add(scene_id)
                unique_scenes.append(scene)
        
        # Limit to 4 scenes max for summary
        unique_scenes = unique_scenes[:4]
        
        for i, scene in enumerate(unique_scenes):
            scene_narrative = self._create_scene_narrative(scene, i + 1, len(unique_scenes))
            script_parts.append(scene_narrative)
        
        # Closing
        script_parts.append("This experience taught me that challenges can become opportunities for growth.")
        
        # Join and clean
        final_script = self._convert_to_first_person("\n".join(script_parts))
        # Don't over-clean the final script - just basic cleanup
        final_script = self._basic_clean_text(final_script)
        
        # Check word count and adjust if needed
        word_count = len(final_script.split())
        if word_count > target_words:
            return self._truncate_script_for_duration(final_script, target_words)
        
        return final_script
    
    def _select_key_scenes(self, scenes: list) -> list:
        """Select key scenes that tell the complete story"""
        if len(scenes) <= 4:
            return scenes
        
        # Always include first and last scenes
        key_scenes = [scenes[0]]
        
        # Add middle scenes
        if len(scenes) > 2:
            middle_index = len(scenes) // 2
            key_scenes.append(scenes[middle_index])
        
        # Add second-to-last scene if it exists
        if len(scenes) > 2:
            key_scenes.append(scenes[-2])
        
        # Always include last scene
        key_scenes.append(scenes[-1])
        
        return key_scenes
    
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
        
        # Fix problematic patterns that might cause "TI" or similar issues
        result = re.sub(r'\btmy\b', 'my', result)  # Fix "tmy" -> "my"
        result = re.sub(r'\bti\b', '', result)  # Remove standalone "ti"
        result = re.sub(r'\bt i\b', '', result)  # Remove "t i"
        
        # Fix "Tmy" -> "This" (common conversion error)
        result = re.sub(r'\bTmy\b', 'This', result)
        result = re.sub(r'\btmy\b', 'this', result)
        
        # Fix "tI" -> "the" (another common conversion error)
        result = re.sub(r'\btI\b', 'the', result)
        result = re.sub(r'\bti\b', 'the', result)
        
        return result
    
    def _clean_title_for_voiceover(self, title: str) -> str:
        """
        Clean a title for safe use in voiceover by removing special characters and formatting
        
        Args:
            title (str): The raw title from storyboard
            
        Returns:
            str: Cleaned title safe for voiceover
        """
        if not title:
            return ""
        
        # Remove common markdown formatting
        cleaned = title.replace('*', '').replace('_', '').replace('`', '')
        
        # Remove quotes and brackets
        cleaned = cleaned.replace('"', '').replace("'", '').replace('[', '').replace(']', '')
        
        # Remove extra whitespace and special characters
        cleaned = re.sub(r'[^\w\s\-]', '', cleaned)
        
        # Clean up multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Ensure it's not empty and has reasonable length
        if len(cleaned) < 2 or len(cleaned) > 50:
            return ""
        
        # Check for common problematic patterns
        if cleaned.lower() in ['ti', 't', 'i', 'story', 'storyboard', 'scene', 'ti a story', 'tmy']:
            return ""
        
        return cleaned
    
    def _clean_text_for_voiceover(self, text: str) -> str:
        """
        Clean text for safe use in voiceover by removing problematic characters and formatting
        
        Args:
            text (str): The raw text to clean
            
        Returns:
            str: Cleaned text safe for voiceover
        """
        if not text:
            return ""
        
        # Remove common markdown formatting
        cleaned = text.replace('*', '').replace('_', '').replace('`', '')
        
        # Remove quotes and brackets
        cleaned = cleaned.replace('"', '').replace("'", '').replace('[', '').replace(']', '')
        cleaned = cleaned.replace('(', '').replace(')', '').replace('{', '').replace('}', '')
        
        # Remove bullet points and special characters
        cleaned = cleaned.replace('•', '').replace('-', ' ').replace('—', ' ').replace('–', ' ')
        
        # Remove extra whitespace and problematic characters
        cleaned = re.sub(r'[^\w\s\.\,\!\?]', ' ', cleaned)
        
        # Clean up multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Ensure it's not empty and has reasonable length
        if len(cleaned) < 2:
            return ""
        
        # Check for common problematic patterns that might cause "TI" or similar issues
        problematic_patterns = ['ti', 't i', 't-i', 't.i', 't/i', 'tmy', 'ti a story', 'tmy is']
        if cleaned.lower().strip() in problematic_patterns:
            return ""
        
        # Additional check for patterns that might appear in the middle of text
        if 'ti a story' in cleaned.lower() or 'tmy is' in cleaned.lower():
            return ""
        
        # Don't filter out legitimate words that contain these patterns
        if cleaned.lower() in ['this', 'that', 'these', 'those', 'their', 'there']:
            return cleaned
        
        return cleaned
    
    def _basic_clean_text(self, text: str) -> str:
        """
        Basic text cleaning for final scripts - less aggressive than _clean_text_for_voiceover
        
        Args:
            text (str): The text to clean
            
        Returns:
            str: Basic cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', text).strip()
        
        # Ensure it's not empty
        if len(cleaned) < 2:
            return ""
        
        return cleaned
    
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
