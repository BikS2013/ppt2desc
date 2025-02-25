import os
from pathlib import Path
from typing import Optional, Union

import PIL.Image
from google import genai
from google.oauth2 import service_account
import logging 

logging.getLogger("google_genai.models").setLevel(logging.WARNING)

class GoogleUnifiedClient:
    """
    A unified client wrapper for Google's GenAI SDK that supports both Gemini API and Vertex AI.
    
    Usage for Gemini API:
        client = GoogleUnifiedClient(api_key="YOUR_KEY", model="gemini-1.5-flash")
        
    Usage for Vertex AI:
        client = GoogleUnifiedClient(
            credentials_path="path/to/credentials.json",
            project_id="your-project-id",
            region="us-central1",
            model="gemini-1.5-pro-002",
            use_vertex=True
        )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        credentials_path: Optional[str] = None,
        project_id: Optional[str] = None,
        region: Optional[str] = None,
        model: Optional[str] = None,
        use_vertex: bool = False,
    ) -> None:
        """
        Initialize the Google GenAI client for either Gemini API or Vertex AI.

        :param api_key: API key for Gemini API (used if use_vertex=False)
        :param credentials_path: Path to service account credentials JSON file (used if use_vertex=True)
        :param project_id: GCP project ID (used if use_vertex=True)
        :param region: GCP region (used if use_vertex=True)
        :param model: The name of the generative model to use
        :param use_vertex: Whether to use Vertex AI (True) or Gemini API (False)
        :raises ValueError: If required parameters are missing
        """
        if model is None:
            raise ValueError("The 'model' argument is required and cannot be None.")
            
        self.model_name = model
        self.use_vertex = use_vertex
        
        if use_vertex:
            # Initialize for Vertex AI
            self.credentials_path = credentials_path or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            if not self.credentials_path:
                raise ValueError(
                    "Credentials path must be provided or set via "
                    "GOOGLE_APPLICATION_CREDENTIALS environment variable."
                )
            if not Path(self.credentials_path).is_file():
                raise FileNotFoundError(
                    f"Credentials file not found at {self.credentials_path}"
                )
            
            self.project_id = project_id or os.environ.get("PROJECT_ID")
            if not self.project_id:
                raise ValueError(
                    "Project ID must be provided or set via PROJECT_ID environment variable."
                )
            
            self.region = region or os.environ.get("REGION")
            if not self.region:
                raise ValueError(
                    "Region must be provided or set via REGION environment variable."
                )
                
            # Load credentials
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path
            ).with_scopes(["https://www.googleapis.com/auth/cloud-platform"])
            
            # Initialize the client for Vertex AI
            self.client = genai.Client(
                vertexai=True,
                project=self.project_id,
                location=self.region,
                credentials=credentials
            )
            
        else:
            # Initialize for Gemini API
            self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
            if not self.api_key:
                raise ValueError(
                    "API key must be provided or set via GEMINI_API_KEY environment variable."
                )
                
            # Initialize the client for Gemini API
            self.client = genai.Client(api_key=self.api_key)

    def generate(self, prompt: str, image_path: Union[str, Path]) -> str:
        """
        Generate content using the Google GenAI model with text + image as input.

        :param prompt: A textual prompt to provide to the model.
        :param image_path: File path (string or Path) to an image to be included in the request.
        :return: The generated response text from the model.
        :raises FileNotFoundError: If the specified image_path does not exist.
        :raises Exception: If the underlying model call fails or an unexpected error occurs.
        """
        # Ensure the image path exists
        image_path_obj = Path(image_path)
        if not image_path_obj.is_file():
            raise FileNotFoundError(f"Image file not found at {image_path_obj}")

        try:
            # Load the image
            image = PIL.Image.open(image_path_obj)
            
            # Generate content using the client.models approach
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, image]
            )
            
            return response.text

        except Exception as e:
            api_type = "Vertex AI" if self.use_vertex else "Gemini API"
            raise Exception(f"Failed to generate content with {api_type} model: {e}")