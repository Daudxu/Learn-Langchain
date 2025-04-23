from typing import TypedDict, Annotated, Sequence, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.memory import Memory
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import operator
import uvicorn
# Load environment variables
load_dotenv()

# Define the state of our graph
class GraphState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    memory: Memory

# Initialize the LLM
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.7,
)

# Create the chat prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful and friendly AI assistant. Be concise and clear in your responses."),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])

# Define the function that processes messages
def process_message(state: GraphState) -> GraphState:
    # Get the most recent message
    messages = state["messages"]
    latest_message = messages[-1]
    
    if not isinstance(latest_message, HumanMessage):
        return state
    
    # Get chat history from memory
    chat_history = state["memory"].get("chat_history", [])
    
    # Create the response
    response = llm.invoke(
        prompt.format(
            chat_history=chat_history,
            input=latest_message.content
        )
    )
    
    # Update memory with the new interaction
    state["memory"].update(
        chat_history=[*chat_history, latest_message, AIMessage(content=response.content)]
    )
    
    # Add AI's response to messages
    return {
        "messages": [*messages, AIMessage(content=response.content)],
        "memory": state["memory"]
    }

# Create the graph
workflow = StateGraph(GraphState)

# Add the node for processing messages
workflow.add_node("process_message", process_message)

# Add the entry point
workflow.set_entry_point("process_message")

# Add the conditional edge
workflow.add_conditional_edges(
    "process_message",
    lambda x: "end" if isinstance(x["messages"][-1], AIMessage) else "process_message",
    {
        "end": END,
        "process_message": "process_message"
    }
)

# Compile the graph
app = workflow.compile()

# FastAPI setup
fastapi_app = FastAPI(title="Chatbot API")

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    session_id: str

# Store sessions
sessions = {}

@fastapi_app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Get or create session
    if request.session_id not in sessions:
        sessions[request.session_id] = {
            "messages": [],
            "memory": Memory()
        }
    
    session = sessions[request.session_id]
    
    # Add the new message to the state
    new_state = {
        "messages": [*session["messages"], HumanMessage(content=request.message)],
        "memory": session["memory"]
    }
    
    # Process the message through the graph
    for response in app.stream(new_state):
        if "messages" in response:
            session["messages"] = response["messages"]
            session["memory"] = response["memory"]
    
    # Get the last AI message
    ai_message = session["messages"][-1].content
    
    return ChatResponse(
        response=ai_message,
        session_id=request.session_id
    )

@fastapi_app.delete("/chat/{session_id}")
async def clear_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
        return {"message": f"Session {session_id} cleared"}
    raise HTTPException(status_code=404, detail="Session not found")

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(fastapi_app, host="0.0.0.0", port=8000) 