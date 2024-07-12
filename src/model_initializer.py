# src/model_initializer.py
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

def initialize_model():
    # Load environment variables from the .env file
    load_dotenv(override=True)

    # Set the environment variables
    openai_api_key = os.getenv("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = openai_api_key

    # Initialize and return the model
    model = ChatOpenAI(model="gpt-4o", temperature=0)
    return model
