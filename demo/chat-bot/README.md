# LangChain + LangGraph Chatbot with FastAPI

This is a chatbot implementation using LangChain, LangGraph, and FastAPI with memory capabilities.

## Features

- LangGraph memory for conversation management
- FastAPI REST API interface
- Session-based conversation management
- OpenAI GPT-3.5 Turbo integration

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Usage

1. Start the server:
   ```bash
   python chatbot.py
   ```

2. The API will be available at `http://localhost:8000`

3. API Endpoints:
   - POST `/chat`: Send a message to the chatbot
     ```json
     {
       "message": "Your message here",
       "session_id": "optional_session_id"
     }
     ```
   - DELETE `/chat/{session_id}`: Clear a specific conversation session

4. API Documentation:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

## How it Works

- The chatbot uses LangGraph for workflow management
- Each session maintains its own conversation memory
- Messages are processed through a graph workflow
- The system maintains state between messages using LangGraph's Memory
- The conversation history is used to provide context for responses 