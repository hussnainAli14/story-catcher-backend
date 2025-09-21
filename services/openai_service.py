import openai
import os
from typing import List, Dict

class OpenAIService:
    def __init__(self):
        self.client = None
        self.api_key = os.getenv('OPENAI_API_KEY')
    
    def _get_client(self):
        """Lazy initialization of OpenAI client"""
        if self.client is None:
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            self.client = openai.OpenAI(api_key=self.api_key)
        return self.client
    
    def generate_story(self, session_data: Dict) -> str:
        """
        Generate a visual storyboard based on user's answers
        """
        try:
            answers = session_data.get('answers', [])
            
            if len(answers) < 4:
                return "I need all four answers to generate your storyboard. Please complete the interview first."
            
            # Format the answers for the prompt
            formatted_answers = self._format_answers_for_prompt(answers)
            
            # Create the prompt for storyboard generation
            prompt = self._create_storyboard_prompt(formatted_answers)
            
            # Generate the storyboard using OpenAI
            response = self._get_client().chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a masterful visual storyteller and storyboard creator who specializes in transforming personal experiences into compelling visual narratives. Your expertise lies in:

1. **Visual Storytelling**: Creating cinematic scenes with clear visual descriptions
2. **Emotional Resonance**: Capturing the emotional journey through visual elements
3. **Scene Structure**: Breaking stories into meaningful scenes with transitions
4. **Mood & Atmosphere**: Describing lighting, sound, and visual mood
5. **Action & Movement**: Creating dynamic visual sequences

Your storyboards should include:
- 4-6 distinct scenes that tell the complete story
- Visual descriptions for each scene
- Mood and atmosphere details
- Sound suggestions
- Smooth transitions between scenes
- A compelling title for the storyboard

Format your response as a complete storyboard with clear scene divisions, visual descriptions, and creative suggestions for bringing the story to life."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1500,
                temperature=0.8
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"I apologize, but I encountered an error while generating your storyboard: {str(e)}"
    
    def _format_answers_for_prompt(self, answers: List[Dict]) -> str:
        """Format answers for the story generation prompt"""
        formatted = ""
        for i, answer in enumerate(answers, 1):
            formatted += f"Question {i}: {answer.get('question', '')}\n"
            formatted += f"Answer: {answer.get('answer', '')}\n\n"
        return formatted
    
    def _create_storyboard_prompt(self, formatted_answers: str) -> str:
        """Create the prompt for storyboard generation"""
        return f"""
Based on the following personal interview responses, create a visual storyboard that brings this person's transformative experience to life:

{formatted_answers}

**Storyboard Requirements:**

1. **Visual Storytelling**: Create 4-6 distinct scenes that tell the complete story with:
   - Clear visual descriptions for each scene
   - Specific settings and environments
   - Character actions and movements
   - Visual composition and framing

2. **Emotional Journey**: Capture the emotional arc through:
   - Mood and atmosphere descriptions
   - Lighting suggestions (warm, cold, dramatic, soft)
   - Color palettes that reflect the emotional tone
   - Visual metaphors that enhance meaning

3. **Cinematic Elements**: Include:
   - Sound suggestions for each scene
   - Transition descriptions between scenes
   - Camera movements and angles
   - Timing and pacing considerations

4. **Authentic Details**: Use the person's specific experience to create:
   - Realistic settings based on their story
   - Authentic character actions and reactions
   - Specific visual elements that honor their unique experience
   - Details that make the story feel personal and real

5. **Creative Formatting**: Structure your response as:
   - A compelling title for the storyboard
   - Clear scene divisions with descriptive headers
   - Visual descriptions that paint a clear picture
   - Suggestions for bringing the storyboard to life (animation, live-action, etc.)

**Format**: Create a complete visual storyboard that could be used for:
- Short animated videos
- Live-action films
- Presentation slides
- Social media content
- Educational materials

Make it visually compelling, emotionally resonant, and true to the person's unique experience. The storyboard should celebrate their journey and the wisdom they've gained.
"""
