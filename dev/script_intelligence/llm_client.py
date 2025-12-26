import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from project root
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / ".env")

class GeminiClient:
    def __init__(self, model_name: Optional[str] = None):
        # 优先使用环境变量 GEMINI_MODEL_NAME，默认设为最新的 3.0 Flash
        self.model_name = model_name or os.getenv("GEMINI_MODEL_NAME", "gemini-3.0-flash")
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found. LLM features disabled.")
            self.model = None
            return

        genai.configure(api_key=self.api_key)
        
        # 使用 2.0/3.0 时代的标准配置
        self.model = genai.GenerativeModel(
            model_name=self.model_name
        )
        logger.info(f"GeminiClient initialized with model: {self.model_name}")

    def generate_content(self, prompt: str) -> str:
        """
        Sends a prompt to the model and returns the text response.
        """
        if not self.model:
            raise RuntimeError("GeminiClient is not properly initialized (missing API Key).")

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return ""

if __name__ == "__main__":
    # Simple test
    client = GeminiClient()
    if client.model:
        print("Testing Gemini API connection...")
        response = client.generate_content("Hello! Are you ready to analyze some screenplays?")
        print(f"Response: {response}")
