import json
import os
import time
from fastapi import FastAPI, HTTPException, Path, Body, Query
from pydantic import BaseModel
from typing import List
import uvicorn
import asyncio
import tiktoken
from packaging import version
import openai
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from functions import bsp_search, consolidated_screening_list_search, trade_leads_search, google_custom_search
from supabase_handlers.supabase_client import SupabaseClient
from supabase_handlers.api_interaction_handler import APIInteractionHandler
from supabase_handlers.thread_handler import ThreadManager
from supabase_handlers.message_handler import MessageHandler
from supabase_handlers.assistant_handler import AssistantManager
from utils.modals.title_manager import TitleMaster
from utils.logger import setup_custom_logger


import logging
from utils.models import AssistantRequest, AssistantUpdateRequest, ThreadCreateRequest, ThreadUpdateRequest, MessageCreateRequest, MessageUpdateRequest 
from typing import Optional
    
# Setup logger
logger = setup_custom_logger(__name__)
logging.getLogger("fastapi").propagate = False
logging.getLogger("uvicorn").propagate = False
logging.getLogger("uvicorn.access").propagate = False

supabase_url = os.environ['SUPABASE_URL']
print("Supabase URL:", supabase_url)  # Add this line
supabase_key = os.environ['SUPABASE_KEY']
api_key = os.environ['OPENAI_API_KEY']
encoding = tiktoken.get_encoding("cl100k_base")




supabase_client = SupabaseClient().client
api_interaction_handler = APIInteractionHandler(),
thread_handler = ThreadManager(api_key)
message_handler = MessageHandler(api_key, thread_handler, api_interaction_handler)
assistant_handler = AssistantManager()



# Initialize FastAPI app
app = FastAPI()
logger.info("FastAPI app initialized.")


app.mount("/static", StaticFiles(directory="static"), name="static")
logger.info("Static files mounted.")


# Init OpenAI client
client = openai.OpenAI(api_key = api_key)

logger.info("OpenAI client initialized.")

origins = [
"http://hermes.markzahm.repl.co/",  # Local frontend server
"https://projecthermes.replit.app/", #production frontend chatbot
"https://assistantadmin.markzahm.repl.co/",  # Production frontend server
"https://modal-id.com/"]



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
    
    

# Create new assistant or load existing
assistant_id = "asst_QKERzUUGiuYO3ZuxYdGJV46q"
logger.info(f"Assistant ID set to {assistant_id}.")

latest_status_messages = {}

# Define request model for chat     endpoint
class ChatRequest(BaseModel):
    thread_id: str
    message: str
    name: Optional[str] = None  # New field for assistant name
    user_id: Optional[str] = None        # New field for user ID
    instructions: Optional[str] = None
    model: Optional[str] = None          # Optional model specification
    tools: Optional[List[dict]] = None
    file_ids: Optional[List[str]] = None


@app.get('/status/{thread_id}')
async def get_status(thread_id: str = Path(..., description="The ID of the thread")):
    if thread_id not in latest_status_messages:
        return {"statusMessage": "No status available for this thread."}
    return {"statusMessage": latest_status_messages[thread_id]}

# Start conversation thread
@app.get('/start')
async def start_conversation(name: Optional[str] = None, user_id: Optional[str] = None):
    logger.info("Starting Conversation...")
    # Pass assistant_name and user_id to the create_thread method
    thread = await thread_handler.create_thread(assistant_id=assistant_id, name=name, user_id=user_id)

    logger.info(f"Conversation started with thread ID: {thread.id}")
    return {"thread_id": thread.id}

# Root endpoint
@app.get("/")
async def root():
    logger.info("Root endpoint called.")
    return FileResponse('static/index.html')

# Chat endpoint to generate response
@app.post('/chat')
async def chat_endpoint(request: ChatRequest):
    global latest_status_messages
    latest_status_messages[request.thread_id] = "Processing your request..."
    logger.info(f"Chat endpoint called with thread ID: {request.thread_id} and message: {request.message}")

    if not request.thread_id:
        raise HTTPException(status_code=400, detail="Missing thread_id")

    # Send user message asynchronously
    await asyncio.to_thread(client.beta.threads.messages.create,
                            thread_id=request.thread_id,
                            role="user",
                            content=request.message)
    logger.info(f"User message sent: {request.message}")
    await message_handler.create_message(thread_id=request.thread_id, role="user", content=request.message, assistant_id=assistant_id, message_id=None )

    # Create and wait for run completion
    run = await asyncio.to_thread(client.beta.threads.runs.create,
                                  thread_id=request.thread_id,
                                  assistant_id=assistant_id,
                                  tools=[{
             "type": "function",
             "function": {
                 "name": "bsp_search",

                 "description": "Get data on Business Service Providers, filtered by category and location.",
                 "parameters": {
                     "type": "object",
                     "properties": {

                         "categories": {
                             "type": "string",
                             "description": "Categories to filter the search"
                         },
                         "ita_offices": {
                             "type": "string",
                             "description": "ITA offices to filter the search"
                         },
                         "size": {
                             "type": "integer",
                             "description": "The number of results to return",
                             "default": 5
                         }
                     },
                     "required": ["q"]
                 }
             }
         },
         {
             "type": "function",
             "function": {
                 "name": "trade_leads_search",
                 "description": "Search for trade leads based on various criteria",
                 "parameters": {
                     "type": "object",
                     "properties": {
                         "q": {
                             "type": "string",
                             "description": "Query string for searching trade leads"
                         },
                         "country_codes": {
                             "type": "string",
                             "description": "Country codes to filter the search"
                         },
                         "tender_start_date_range_from": {
                             "type": "string",
                             "format": "date",
                             "description": "Start date for tender date range"
                         },
                         "tender_start_date_range_to": {
                             "type": "string",
                             "format": "date",
                             "description": "End date for tender date range"
                         },
                         "contract_start_date_range_from": {
                             "type": "string",
                             "format": "date",
                             "description": "Start date for contract date range"
                         },
                         "contract_start_date_range_to": {
                             "type": "string",
                             "format": "date",
                             "description": "End date for contract date range"
                         },
                         "size": {
                             "type": "integer",
                             "description": "Number of results to return"
                         },
                         "offset": {
                             "type": "integer",
                             "description": "Offset for pagination"
                         }
                     },
                     "required": ["q"]
                 }
             }
         },

         {
             "type": "function",
             "function": {
                 "name": "consolidated_screening_list_search",
                 "description": "Search the Consolidated Screening List",
                 "parameters": {
                     "type": "object",
                     "properties": {
                         "name": {"type": "string", "description": "Name to search for"},
                         "fuzzy_name": {"type": "string", "description": "Fuzzy name to search for"},
                         "sources": {"type": "string", "description": "Specific sources to search within"},
                         "types": {"type": "string", "description": "Types of entities to search for"},
                         "countries": {"type": "string", "description": "Countries associated with the entities"},
                         "address": {"type": "string", "description": "Address of the entity"},
                         "city": {"type": "string", "description": "City associated with the entity"},
                         "state": {"type": "string", "description": "State associated with the entity"},
                         "postal_code": {"type": "string", "description": "Postal code associated with the entity"},
                         "full_address": {"type": "string", "description": "Full address to search for"},
                         "offset": {"type": "integer", "description": "Offset for pagination"},
                         "size": {"type": "integer", "description": "Number of results to return"}
                     },
                     "required": []
                 }
             }
         },
         {
             "type": "function",
             "function": {
                 "name": "google_custom_search",
                 "description": "Perform a custom Google search.",
                 "parameters": {
                     "type": "object",
                     "properties": {
                         "query": {"type": "string", "description": "Search query string"}
                     },
                     "required": ["query"]
                 }
             }
         }
     ])  # your tools configuration
    logger.info(f"Run created with ID: {run.id}")
    tool_functions = {
        "bsp_search": bsp_search,
        "consolidated_screening_list_search": consolidated_screening_list_search,
        "trade_leads_search": trade_leads_search,
        "google_custom_search": google_custom_search
    }

    tool_status_messages = {
        "bsp_search": "Checking Business Service Providers...",
        "consolidated_screening_list_search": "Searching entities on the Screening List...",
        "trade_leads_search": "Looking for leads...",
        "google_custom_search": "Searching trade.gov..."
    }
    # Wait for run completion or required action
    while True:
        run_status = await asyncio.to_thread(client.beta.threads.runs.retrieve,
                                             thread_id=request.thread_id,
                                             run_id=run.id)
        logger.info(f"Checking run status: {run_status.status}")

        if run_status.status == 'completed':
            latest_status_messages[request.thread_id] = "Processing complete."
            logger.info("Run completed.")
            break
        elif run_status.status == 'requires_action' and run_status.required_action:
            tool_outputs = []
            for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:
                tool_name = tool_call.function.name
                tool_function = tool_functions[tool_name]

                # Update the status message based on the tool being called
                current_status_message = tool_status_messages.get(tool_name, "Processing your request...")
                latest_status_messages[request.thread_id] = current_status_message
                logger.info(f"Status message for tool {tool_name}: {current_status_message}")

                call_id = tool_call.id
                logger.info(f"Handling tool call: {tool_name}")
                logger.debug(f"Tool Call Arguments: {json.loads(tool_call.function.arguments)}")

                if tool_function:
                    arguments = json.loads(tool_call.function.arguments)
                    try:
                        # Check if the tool function is a coroutine function
                        if asyncio.iscoroutinefunction(tool_functions[tool_name]):
                            output = await tool_functions[tool_name](**arguments)
                        else:
                            output = await asyncio.to_thread(tool_functions[tool_name], **arguments)

                        logger.info(f"Tool output: {output}")

                        tool_outputs.append({
                            "tool_call_id": call_id,
                            "output": json.dumps(output)
                        })
                        latest_status_messages[request.thread_id] = "Awaiting response..."
                    except Exception as e:
                        logger.error(f"An error occurred while executing {tool_name}: {e}")
                else:
                    logger.warning(f"No function defined for tool: {tool_name}")

            if tool_outputs:
                await asyncio.to_thread(client.beta.threads.runs.submit_tool_outputs,
                                        thread_id=request.thread_id,
                                        run_id=run.id,
                                        tool_outputs=tool_outputs)

        elif run_status.status == 'expired':
            logger.info("Run expired. Informing user and suggesting restart.")
            return {"response": "Our conversation timed out. Would you like to start over?"}
# Return None to indicate expiration

        await asyncio.sleep(2)  # Non-blocking sleep

    # Retrieve messages and process annotations asynchronously
    try:
        messages = await asyncio.to_thread(client.beta.threads.messages.list,
                                           thread_id=request.thread_id)
        logger.info(f"Number of messages retrieved: {len(messages.data)}")
        for msg in messages.data:
            logger.info(f"Message ID: {msg.id}, Role: {msg.role}, Content: {msg.content[0].text.value}")

        if messages.data:
            latest_message = messages.data[0]  # Get the most recent message
            if latest_message.role == "assistant":
                assistant_response = latest_message.content[0].text.value
                assistant_message_id = latest_message.id
                logger.info(f"Assistant's latest response: {assistant_response}")
                await message_handler.create_message(thread_id=request.thread_id, role="assistant", message_id=assistant_message_id, content=assistant_response, assistant_id=assistant_id)
            else:
                logger.info("Most recent message not from assistant.")
                assistant_response = "No recent assistant response found."
        else:
            logger.info("No messages found in the thread.")
            assistant_response = "No response received."
    except Exception as e:
        logger.error(f"Error while processing messages: {e}")
        assistant_response = "Error in processing response."

    latest_status_messages[request.thread_id] = "Processing complete."
    logger.info("Run completed.")
    return {"response": assistant_response}



# ASSISTANT MANAGER ENDPOINTS

@app.post("/assistants/create")
async def create_assistant_endpoint(request: Optional[AssistantRequest]):
    if request is None:
        raise HTTPException(status_code=400, detail="Request body is missing")
    return await assistant_handler.create_assistant(request.model, request.instructions, request.name, request.file_ids)

@app.put("/assistants/{assistant_id}/update")
async def update_assistant_endpoint(assistant_id: str, request: AssistantUpdateRequest):
    return await assistant_handler.update_assistant(assistant_id, request.model, request.instructions, request.name, request.file_ids)

@app.get("/assistants/{assistant_id}")
async def get_assistant_endpoint(assistant_id: str):
    return await assistant_handler.get_assistant(assistant_id)

@app.get("/assistants")
async def list_assistants_endpoint(start_date: Optional[str], end_date: Optional[str], limit: int):
    return await assistant_handler.list_assistants(start_date, end_date, limit)

@app.delete("/assistants/{assistant_id}/delete")
async def delete_assistant_endpoint(assistant_id: str):
    result = await assistant_handler.delete_assistant(assistant_id)
    if result:
        return {"detail": "Assistant deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Assistant not found")


# THREAD MANAGER ENDPOINTS


@app.post("/threads")
async def create_thread(request: Optional[ThreadCreateRequest] = None):
    return await thread_handler.create_thread(request.assistant_id, request.assistant_name, request.user_id, request.user_name)

@app.get("/threads/{thread_id}")
async def get_thread(thread_id: str):
    return await thread_handler.get_thread(thread_id)

@app.get("/threads")
async def list_threads(start_date: Optional[str], end_date: Optional[str], limit: int):
    return await thread_handler.list_threads(start_date, end_date, limit)

@app.put("/threads/{thread_id}")
async def update_thread(thread_id: str, request: ThreadUpdateRequest):
    return await thread_handler.update_thread(thread_id, request.status, request.assistant_name)

@app.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str):
    return await thread_handler.delete_thread(thread_id)

# MESSAGE MANAGER ENDPOINTS

@app.post("/messages")
async def create_message(request: MessageCreateRequest):
    return await message_handler.create_message(request.name, request.thread_id, request.role, request.content, request.assistant_id, request.user_id)

@app.get("/messages/{thread_id}/{message_id}")
async def get_message(thread_id: str, message_id: str):
    return await message_handler.retrieve_message(thread_id, message_id)

@app.put("/messages/{thread_id}/{message_id}")
async def update_message(thread_id: str, message_id: str, request: MessageUpdateRequest):
    return await message_handler.modify_message(thread_id, message_id, request.new_content)

@app.get("/messages/{thread_id}")
async def list_messages(thread_id: str):
    return await message_handler.list_messages(thread_id)


# Run server using Uvicorn
if __name__ == '__main__':
    logger.info("Starting Uvicorn server...")
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True, reload_dirs=["main"])
    