import os
import google.generativeai as genai
from dotenv import load_dotenv

class GeminiClient:
    def __init__(self, api_key=None, model_name='gemini-2.0-flash'):
        load_dotenv()
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API Key not found. Please set GOOGLE_API_KEY environment variable or pass it to the constructor.")
        
        genai.configure(api_key=self.api_key)
        self.model_name = model_name
        self.model = genai.GenerativeModel(self.model_name)

    def generate_content(self, prompt, generation_config=None):
        """Generates content based on a text prompt."""
        try:
            response = self.model.generate_content(prompt, generation_config=generation_config)
            return response.text
        except Exception as e:
            return f"Error generating content: {e}"

    def start_chat(self, history=None):
        """Starts a chat session."""
        return self.model.start_chat(history=history or [])

    def send_message(self, chat_session, message):
        """Sends a message in a chat session."""
        try:
            response = chat_session.send_message(message)
            return response.text
        except Exception as e:
            return f"Error sending message: {e}"

    def get_model_list(self):
        """Lists available models."""
        return [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
