import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables from the .env file
load_dotenv(override=True)

# Now the environment variables are available
tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2")
langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

# Set the environment variables
os.environ["OPENAI_API_KEY"] = openai_api_key

# Initialize the model
model = ChatOpenAI(model="gpt-4o", temperature=0)
