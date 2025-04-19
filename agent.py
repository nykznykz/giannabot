from langgraph.checkpoint.memory import MemorySaver 
from typing import Annotated, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults

from langchain_google_community import CalendarToolkit
from langchain_google_community import GmailToolkit
from langchain_google_community.calendar.utils import get_google_credentials
from langchain_google_community.gmail.utils import (
    build_resource_service,
    get_gmail_credentials,
)

from langchain_community.tools import YouTubeSearchTool
from sound_tool import SoundTool

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from dotenv import load_dotenv
import os
import logging

# load environment variables
load_dotenv()

# Define the system prompt
SYSTEM_PROMPT = f"""
You are Gianna, a witty, cheerful, and helpful AI assistant living inside a Telegram bot. Your job is to make {os.getenv("MY_NAME")}'s life smoother, happier, and more fun. You’re smart, quirky, and always ready with a good-natured joke (but never overdo it). You know when to be serious and when to lighten the mood.

Key facts to remember:

Your boss and bestie is {os.getenv("MY_NAME")}. You assist him with all sorts of tasks, especially calendar scheduling, reminders, web research, summarizing stuff, and sending emails.

{os.getenv("MY_NAME")}'s girlfriend is {os.getenv("GF_NAME")}. Be friendly and respectful when talking about her or interacting on her behalf.

When sending emails or creating calendar events:

Use {os.getenv("MY_EMAIL")} for {os.getenv("MY_NAME")}.

Use {os.getenv("GF_EMAIL")} for {os.getenv("GF_NAME")} when appropriate.


To facilitate a more engaging style of learning / communication, when appropriate and relevant, include links to youtube videos in your responses. 

Do not list links from memory as they may be outdated! Always use the youtube_search tool to search for videos on YouTube to illustrate your points. 


Teaching Chinese:
{os.getenv("MY_NAME")} occasionally asks you to teach him chinese. 
If {os.getenv("MY_NAME")} provides an English phrase / sentence, translate it into Chinese and include pinyin so he knows how to pronounce it. 
If {os.getenv("MY_NAME")} provides a Chinese phrase / sentence, translate it into English and include pinyin so he knows how to pronounce it. 


If you’re not sure about something, ask {os.getenv("MY_NAME")} rather than guessing.

Don’t hallucinate. Stick to what you know or what you’re told.

Be Gianna: bubbly but reliable, playful but professional. Keep responses concise and to the point.


Your mission: Make life easier for {os.getenv("MY_NAME")}, with charm, humor, and solid productivity chops. Let's roll.


"""


class State(TypedDict):
    messages: Annotated[list, add_messages]

def chatbot(state: State):
    # Add system message at the start of the messages list
    messages = [
        ("system", SYSTEM_PROMPT)
    ] + state["messages"]
    
    return {"messages": [llm_with_tools.invoke(messages)]}

# Initialize LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=os.environ.get("OPENAI_API_KEY")
).bind(
    system_message=SYSTEM_PROMPT
)

# Create the search tool with API key from environment
search_tool = TavilySearchResults(
    max_results=2,
    tavily_api_key=os.getenv("TAVILY_API_KEY")
)


def create_google_tools():


    # Define all required scopes upfront
    SCOPES = [
        "https://www.googleapis.com/auth/calendar",  # Calendar scopes
        "https://www.googleapis.com/auth/calendar.events",
        "https://mail.google.com/"  # Gmail scope for full access
    ]

    # Get credentials with all required scopes

    credentials = get_google_credentials(
        token_file="token.json",
        scopes=SCOPES,
        client_secrets_file="credentials.json"
    )

    # Build API resources for both services
    gmail_api_resource = build_resource_service(credentials=credentials)
    calendar_api_resource = build_resource_service(credentials=credentials)

    # Initialize toolkits with their respective API resources
    gmail_toolkit = GmailToolkit(api_resource=gmail_api_resource)
    calendar_toolkit = CalendarToolkit(calendar_api=calendar_api_resource)

    # Get tools
    gmail_tools = gmail_toolkit.get_tools()
    calendar_tools = calendar_toolkit.get_tools()
    return gmail_tools, calendar_tools

gmail_tools, calendar_tools = create_google_tools()

class CustomYouTubeSearchTool(YouTubeSearchTool):
    description:str = """Useful for searching YouTube videos to illustrate points or provide visual examples.
    Input should be a search query for YouTube videos.
    The tool will return relevant video links and titles that match the search query.
    Use this tool when you want to find educational or explanatory videos to share with the user."""

youtube_search_tool = CustomYouTubeSearchTool()

# Store chat memories for different conversations
chat_memories = {}

def create_agent():
    graph_builder = StateGraph(State)
    
    # Initialize the sound tool
    sound_tool = SoundTool()
    
    # Combine all tools
    tools = [search_tool, youtube_search_tool, sound_tool] + calendar_tools + gmail_tools
    global llm_with_tools
    llm_with_tools = llm.bind_tools(tools)
    
    # Add nodes
    graph_builder.add_node("chatbot", chatbot)
    
    # Add tool node
    tool_node = ToolNode(tools=tools)
    graph_builder.add_node("tools", tool_node)
    
    # Add conditional edges
    graph_builder.add_conditional_edges(
        source="chatbot",
        path=tools_condition,
    )
    # Any time a tool is called, we return to the chatbot to decide the next step
    graph_builder.add_edge("tools", "chatbot")
    
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_edge("chatbot", END)
    
    memory = MemorySaver()
    return graph_builder.compile(checkpointer=memory)

def get_agent_response(message: str, chat_id: str, context_message: Optional[str] = None) -> str:
    """
    Get a response from the agent for a given message and chat context.
    
    Args:
        message (str): The user's message
        chat_id (str): The chat ID to maintain separate conversation histories
        context_message (Optional[str]): The message being replied to, if any
    
    Returns:
        str: The agent's response
    """
    # Initialize memory for new chats
    if chat_id not in chat_memories:
        chat_memories[chat_id] = create_agent()
    
    # Create the input messages
    messages = []
    if context_message:
        messages.append(HumanMessage(content=context_message))
        messages.append(AIMessage(content="I understand you're referring to this previous message."))
    
    messages.append(HumanMessage(content=message))
    
    # Get response from the agent
    events = chat_memories[chat_id].stream(
        input={"messages": messages},
        config={"configurable": {"thread_id": chat_id}},
        stream_mode="values",
    )
    
    # Get the last response
    final_response = None
    for event in events:
        if event["messages"]:
            final_response = event["messages"][-1].content
    
    return final_response or "I apologize, but I couldn't generate a response."

if __name__ == "__main__":
    # Test the contact and calendar functionality
    test_chat_id = "test_integration"
    
    # print("\nTest 1: Personality test...")
    # response = get_agent_response("Introduce yourself to me", test_chat_id)
    # print("\nResponse:")
    # print(response)

    # # Test 3: Create a calendar event with the contact
    # print("\nTest 3: Creating a calendar event with contact...")
    # response = get_agent_response("what are my calendar events for next week?", test_chat_id)
    # print("\nResponse:")
    # print(response)

    # # Test 2: Retreive email
    # print("\nTest 2: Retreiving email...")
    # response = get_agent_response("Any emails from sunriseclick?", test_chat_id)
    # print("\nResponse:")
    # print(response)

    # Test 4: Search YouTube
    # print("\nTest 4: Searching YouTube...")
    # response = get_agent_response("how to install a new toilet", test_chat_id)
    # print("\nResponse:")
    # print(response)

    # Test 5: Send sound
    print("\nTest 5: Sending sound...")
    response = get_agent_response("how do I say Im interested in this project in chinese?", test_chat_id)
    print("\nResponse:")
    print(response)