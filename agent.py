from langchain_community.llms import Ollama
from langchain_community.tools.tavily_search import TavilySearchResults
from calendar_tool import GoogleCalendarTool
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Create the Ollama model instance
model = Ollama(
    model="gemma3:4b",
    base_url="http://localhost:11434"
)

# Create the search tool with API key from environment
search = TavilySearchResults(
    max_results=2,
    tavily_api_key=os.getenv("TAVILY_API_KEY")
)

# Create the Google Calendar tool
calendar_tool = GoogleCalendarTool()

# Combine all tools
tools = [search, calendar_tool]

# Create a memory instance for each chat
chat_memories = {}

def get_agent_response(message: str, chat_id: str) -> str:
    """
    Get a response from the agent for a given message.
    
    Args:
        message (str): The user's message
        chat_id (str): The chat ID to maintain conversation history
        
    Returns:
        str: The agent's response
    """
    # Get or create memory for this chat
    if chat_id not in chat_memories:
        chat_memories[chat_id] = ConversationBufferMemory(memory_key="chat_history")
    
    # Create agent with this chat's memory
    agent = initialize_agent(
        tools=tools,
        llm=model,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=True,
        memory=chat_memories[chat_id]
    )
    
    # Get response from agent
    response = agent.run(message)
    return response

if __name__ == "__main__":
    # Example usage
    test_message = "What's the latest news about AI?"
    response = get_agent_response(test_message, "test_chat")
    print(f"User: {test_message}")
    print(f"Agent: {response}") 