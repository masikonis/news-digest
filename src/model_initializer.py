# src/model_initializer.py
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

class ModelManager:
    def __init__(self):
        # Load environment variables
        load_dotenv(override=True)
        openai_api_key = os.getenv("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = openai_api_key
        
        # Initialize different models
        self.models = {
            'basic': ChatOpenAI(model="gpt-4o-mini", temperature=0),
            'advanced': ChatOpenAI(model="gpt-4o", temperature=0),
            'embeddings': None  # We'll add this later when needed
        }
    
    def get_model(self, purpose: str):
        """Get the appropriate model for a specific purpose."""
        if purpose not in self.models:
            raise ValueError(f"Unknown model purpose: {purpose}")
        return self.models[purpose]

def initialize_model(purpose: str = 'summary'):
    """Get a model for specific purpose. Defaults to summary model."""
    manager = ModelManager()
    return manager.get_model(purpose)
