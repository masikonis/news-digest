import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, SystemMessage

# Load environment variables from the .env file
load_dotenv()

# Now the environment variables are available
tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2")
langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

# Set the OPENAI_API_KEY environment variable
os.environ["OPENAI_API_KEY"] = openai_api_key

# Initialize the model
model = ChatOpenAI(model="gpt-4")

# Define the system template for the prompt
system_template = "Provide one random news headline from {country}."

# Create the prompt template
prompt_template = ChatPromptTemplate.from_messages(
    [("system", system_template), ("user", "")]
)

# Create the output parser
parser = StrOutputParser()

# Combine the prompt template, model, and parser into a chain
chain = prompt_template | model | parser

# Define the input variables for the prompt
input_vars = {"country": "Lithuania"}

# Invoke the chain with the input variables
response = chain.invoke(input_vars)

# Print the simplified response
print(response)
