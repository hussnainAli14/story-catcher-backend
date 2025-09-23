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
                        "content": """You are a masterful visual storyteller and storyboard creator who specializes in transforming personal experiences into compelling visual narratives. 

CRITICAL: You MUST format your storyboard response EXACTLY as specified in the user's prompt. Follow the exact structure with:
- **Storyboard: "[Title]" – [Subtitle]** header
- **Scene X: "[Scene Name]"** for each scene
- Bullet points (•) for each element (Visual, Setting/Action, Mood, Sound, Transition)
- Proper spacing and formatting
- 4-6 scenes total

Your expertise lies in:
1. **Visual Storytelling**: Creating cinematic scenes with clear visual descriptions
2. **Emotional Resonance**: Capturing the emotional journey through visual elements
3. **Scene Structure**: Breaking stories into meaningful scenes with transitions
4. **Mood & Atmosphere**: Describing lighting, sound, and visual mood
5. **Action & Movement**: Creating dynamic visual sequences

IMPORTANT: Follow the exact formatting template provided in the user prompt. Do not deviate from the specified structure."""
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

**IMPORTANT FORMATTING REQUIREMENTS:**

Create a storyboard with this EXACT structure and formatting:

**Storyboard: "[Title]" – [Subtitle]**

**Scene 1: "[Scene Name]"**
• **Visual**: [Detailed visual description]
• **Setting**: [Location and environment details]
• **Mood**: [Emotional tone and atmosphere]
• **Sound**: [Audio suggestions]
• **Transition**: [How this scene connects to the next]

**Scene 2: "[Scene Name]"**
• **Visual**: [Detailed visual description]
• **Action**: [Key actions and movements]
• **Mood**: [Emotional tone and atmosphere]
• **Sound**: [Audio suggestions]
• **Transition**: [How this scene connects to the next]

**Scene 3: "[Scene Name]"**
• **Visual**: [Detailed visual description]
• **Setting**: [Location and environment details]
• **Mood**: [Emotional tone and atmosphere]
• **Sound**: [Audio suggestions]
• **Transition**: [How this scene connects to the next]

**Scene 4: "[Scene Name]"**
• **Visual**: [Detailed visual description]
• **Action**: [Key actions and movements]
• **Mood**: [Emotional tone and atmosphere]
• **Sound**: [Audio suggestions]
• **Transition**: [How this scene connects to the next]

**Scene 5: "[Scene Name]"**
• **Visual**: [Detailed visual description]
• **Setting**: [Location and environment details]
• **Mood**: [Emotional tone and atmosphere]
• **Sound**: [Audio suggestions]
• **Transition**: [How this scene connects to the next]

**Scene 6: "[Scene Name]"**
• **Visual**: [Detailed visual description]
• **Action**: [Key actions and movements]
• **Mood**: [Emotional tone and atmosphere]
• **Sound**: [Audio suggestions]
• **Transition**: [Conclusion or final transition]

**Storyboard Guidelines:**
- Use bullet points (•) for each element
- Keep descriptions concise but vivid
- Focus on visual storytelling
- Include specific details from their story
- Create emotional resonance through mood and sound
- Make it suitable for video/animation production

**Requirements:**
- Create 4-6 scenes total
- Each scene should have Visual, Setting/Action, Mood, Sound, and Transition
- Use the person's specific experience details
- Make it visually compelling and emotionally resonant
- Format exactly as shown above with proper spacing and bullet points
"""
