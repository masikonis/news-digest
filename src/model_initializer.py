# src/model_initializer.py
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

class ModelManager:
    def __init__(self):
        load_dotenv(override=True)
        openai_api_key = os.getenv("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = openai_api_key
        
        # Initialize model configurations
        self.model_configs = {
            'basic': {"model": "gpt-4o-mini"},
            'advanced': {"model": "gpt-4o"},
            'embeddings': {
                "model": "text-embedding-3-small",
                "dimensions": 1536
            }
        }
    
    def get_model(self, purpose: str, temperature: float = 0):
        if purpose not in self.model_configs:
            raise ValueError(f"Unknown model purpose: {purpose}")
            
        config = self.model_configs[purpose]
        if config is None:
            return None
            
        if purpose == 'embeddings':
            return OpenAIEmbeddings(
                model=config["model"],
                dimensions=config["dimensions"]
            )
            
        return ChatOpenAI(model=config["model"], temperature=temperature)

def initialize_model(purpose: str = 'summary', temperature: float = 0):
    manager = ModelManager()
    return manager.get_model(purpose, temperature)
