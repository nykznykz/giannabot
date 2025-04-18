from langgraph.checkpoint.memory import MemorySaver 
from typing import Annotated, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

class State(TypedDict):
    messages: Annotated[list, add_messages]

def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

# Initialize LLM
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0,
    api_key=os.environ.get("OPENAI_API_KEY")
)

# Create the search tool with API key from environment
search_tool = TavilySearchResults(
    max_results=2,
    tavily_api_key=os.getenv("TAVILY_API_KEY")
)

# Store chat memories for different conversations
chat_memories = {}

def create_agent():
    graph_builder = StateGraph(State)
    
    # Combine all tools
    tools = [search_tool]
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