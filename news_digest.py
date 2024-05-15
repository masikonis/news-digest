import os
from dotenv import load_dotenv
from langchain_openai import OpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain

# Load environment variables from the .env file
load_dotenv()

# Get the API key from the environment variable
api_key = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI language model
llm = OpenAI(api_key=api_key)

# Define a custom prompt for summarizing news
prompt = PromptTemplate(
    template="Summarize the following news article:\n\n{text}\n\nSummary:",
    input_variables=["text"]
)

# Define a simple chain for summarizing news
class NewsSummaryChain(LLMChain):
    def __init__(self, llm, prompt):
        super().__init__(llm=llm, prompt=prompt)

# Create an instance of the chain
summary_chain = NewsSummaryChain(llm=llm, prompt=prompt)

# Function to simulate reading news (you can replace this with actual news reading logic)
def read_news():
    return "Your news article text here."

# Run the chain with a news article
news_article = read_news()
summary = summary_chain.invoke({"text": news_article})
print("News Summary:")
print(summary)
