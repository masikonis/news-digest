import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_functions_agent

# Load environment variables from the .env file
load_dotenv()

# Now the environment variables are available
tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2")
langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
tavily_api_key = os.getenv("TAVILY_API_KEY")

# Set the environment variables
os.environ["OPENAI_API_KEY"] = openai_api_key
os.environ["TAVILY_API_KEY"] = tavily_api_key

# Initialize the Tavily search tool
tavily_tool = TavilySearchResults()

# Initialize the model
model = ChatOpenAI(model="gpt-4o", temperature=0)

# Define the system template for the prompt
system_template = "Provide one random news headline from {country} (no older than 7 days)."

# Create the prompt template
prompt_template = ChatPromptTemplate.from_messages([
    ("system", system_template),
    ("user", "")
])

# Create the output parser
parser = StrOutputParser()

# Combine the prompt template, model, and parser into a chain
chain = prompt_template | model | parser

# Define the input variables for the prompt
input_vars = {"country": "Lithuania"}

# Use the Tavily tool to get the latest news headline
tool_query = "latest news headline from Lithuania"
tool_response = tavily_tool.invoke({"query": tool_query})

# Print the headline fetched using Tavily
print("Latest news headline (via Tavily):", tool_response)

# Create the base prompt using LangSmith hub
instructions = """You are an assistant."""
base_prompt = hub.pull("langchain-ai/openai-functions-template")
prompt = base_prompt.partial(instructions=instructions)

# Create an agent with the model and tools
agent = create_openai_functions_agent(model, [tavily_tool], prompt)
agent_executor = AgentExecutor(agent=agent, tools=[tavily_tool], verbose=True)

# Invoke the chain with the input variables and get response
response = agent_executor.invoke({"input": "Provide one random news headline from Lithuania."})

# Print the response from the model
print("Response from model:", response["output"])
