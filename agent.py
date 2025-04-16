from langchain_community.llms import Ollama
from langchain_community.tools.tavily_search import TavilySearchResults
from calendar_tool import GoogleCalendarTool
from contact_tool import ContactTool
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
import os
import logging

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

# Create the contact lookup tool
contact_tool = ContactTool()

# Combine all tools
tools = [search, calendar_tool, contact_tool]

# Create a memory instance for each chat
chat_memories = {}

def get_agent_response(message: str, chat_id: str, context_message: str = None) -> str:
    """Get response from the agent with conversation history."""
    try:
        # Initialize memory for this chat if not exists
        if chat_id not in chat_memories:
            chat_memories[chat_id] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="output"
            )
        
        # Format the input with context if available
        if context_message:
            formatted_message = f"Context from previous message: {context_message}\n\nUser message: {message}"
        else:
            formatted_message = message
            
        # Create agent with this chat's memory
        agent = initialize_agent(
            tools=tools,
            llm=model,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=True,
            memory=chat_memories[chat_id],
            handle_parsing_errors=True
        )
        
        # Get response from agent
        response = agent.run(formatted_message)
        
        # Update memory with the interaction
        chat_memories[chat_id].save_context(
            {"input": formatted_message},
            {"output": response}
        )
        
        return response
    except Exception as e:
        logging.error(f"Error in get_agent_response: {e}")
        return "I encountered an error processing your request. Please try again."

if __name__ == "__main__":
    # Example usage
    test_message = "What's the latest news about AI?"
    response = get_agent_response(test_message, "test_chat")
    print(f"User: {test_message}")
    print(f"Agent: {response}") 