# src/model_initializer.py
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI

class ModelManager:
    def __init__(self):
        load_dotenv(override=True)
        
        # Initialize OpenAI
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:  # Only set if not None
            os.environ["OPENAI_API_KEY"] = openai_api_key
        
        # Initialize Gemini
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        
        # Initialize model configurations
        self.model_configs = {
            'openai': {
                'basic': {"model": "gpt-4o-mini"},
                'advanced': {"model": "gpt-4o"},
                'embeddings': {
                    "model": "text-embedding-3-small",
                    "dimensions": 1536
                }
            },
            'gemini': {
                'basic': {"model": "gemini-1.5-pro"},
                'advanced': {"model": "gemini-2.0-flash-exp"},
                'embeddings': {
                    "model": "text-embedding-004",
                    "dimensions": 768
                }
            }
        }
    
    def get_model(self, purpose: str, temperature: float = 0, provider: str = "openai"):
        if provider not in self.model_configs:
            raise ValueError(f"Unknown provider: {provider}")
            
        provider_configs = self.model_configs[provider]
        if purpose not in provider_configs:
            raise ValueError(f"Unknown model purpose: {purpose}")
            
        config = provider_configs[purpose]
        if config is None:
            return None
            
        if provider == "gemini":
            if not self.gemini_api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
            if purpose == 'embeddings':
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                return GoogleGenerativeAIEmbeddings(
                    model=f"models/{config['model']}",
                    google_api_key=self.gemini_api_key
                )
            return ChatGoogleGenerativeAI(
                model=config["model"],
                google_api_key=self.gemini_api_key,
                temperature=temperature
            )
            
        if purpose == 'embeddings':
            return OpenAIEmbeddings(
                model=config["model"],
                dimensions=config["dimensions"]
            )
            
        return ChatOpenAI(model=config["model"], temperature=temperature)

def initialize_model(purpose: str = 'basic', temperature: float = 0, provider: str = "openai"):
    manager = ModelManager()
    return manager.get_model(purpose, temperature, provider)
