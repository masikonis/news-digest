# src/model_initializer.py
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

class ModelManager:
    """Manages AI model initialization and configuration.

    A singleton-like class that handles the initialization and configuration
    of different AI models based on their intended purpose.

    Attributes:
        model_configs (Dict[str, Dict]): Configuration settings for different model types
            - 'basic': For simple tasks using gpt-4o-mini
            - 'advanced': For complex tasks using gpt-4o
            - 'embeddings': Reserved for future embedding models
    """

    def __init__(self):
        """Initialize the ModelManager and load necessary configurations.

        Loads OpenAI API key from environment variables and sets up basic
        model configurations. Uses dotenv for environment variable management.

        Raises:
            EnvironmentError: If OPENAI_API_KEY is not found in environment
        """
        # Load environment variables
        load_dotenv(override=True)
        openai_api_key = os.getenv("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = openai_api_key
        
        # Initialize model configurations (not instances)
        self.model_configs = {
            'basic': {"model": "gpt-4o-mini"},
            'advanced': {"model": "gpt-4o"},
            'embeddings': None  # We'll add this later when needed
        }
    
    def get_model(self, purpose: str, temperature: float = 0):
        """Get an initialized AI model for a specific purpose.

        Args:
            purpose (str): The intended use of the model ('basic', 'advanced', or 'embeddings')
            temperature (float, optional): Model temperature setting. Defaults to 0.
                0 is more deterministic, 1 is more creative.

        Returns:
            ChatOpenAI: Initialized model instance, or None if purpose is 'embeddings'

        Raises:
            ValueError: If the specified purpose is not found in model_configs
        """
        if purpose not in self.model_configs:
            raise ValueError(f"Unknown model purpose: {purpose}")
            
        config = self.model_configs[purpose]
        if config is None:
            return None
            
        return ChatOpenAI(model=config["model"], temperature=temperature)

def initialize_model(purpose: str = 'summary', temperature: float = 0):
    """Factory function to get an initialized AI model.

    A convenience function that creates a ModelManager instance and returns
    an appropriate model based on the specified purpose.

    Args:
        purpose (str, optional): The intended use of the model. Defaults to 'summary'.
        temperature (float, optional): Model temperature setting. Defaults to 0.
            Lower values make the output more deterministic.

    Returns:
        ChatOpenAI: Initialized model instance, or None if purpose is 'embeddings'

    Raises:
        ValueError: If the specified purpose is not supported
    """
    manager = ModelManager()
    return manager.get_model(purpose, temperature)
