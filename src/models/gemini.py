import google.generativeai as genai
from typing import Optional
import PIL.Image
import os

class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model: str = None):
        """Initialize Gemini client with API key.
        
        Args:
            api_key: Optional API key. If not provided, will check environment variable GEMINI_API_KEY.
            model: Name of the generative model to use. This is a required argument.
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("API key must be provided either through constructor or GEMINI_API_KEY environment variable")
        
        if model is None:
            raise ValueError("The 'model' argument is required and cannot be None.")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model)
        self.model_name = model

    def generate(self, prompt: str, image_path: str) -> str:
        """Generate content using Gemini model with an image input.
        
        Args:
            prompt: The textual prompt to provide to the model.
            image_path: The file path to the image to be included in the request.
        
        Returns:
            The generated response text.
        """
        image = PIL.Image.open(image_path)
        response = self.model.generate_content([prompt, image])
        return response
