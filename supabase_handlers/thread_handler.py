import logging
from datetime import datetime
import time
import asyncio
from typing import Optional
from pytz import timezone
from openai import OpenAI
from supabase_handlers.supabase_client import SupabaseClient
from supabase_handlers.api_interaction_handler import APIInteractionHandler

def get_local_time():
    local_time = datetime.now(timezone('America/New_York'))
    return local_time.strftime("%Y-%m-%d %H:%M:%S")


class ThreadManager(SupabaseClient):
    def __init__(self, api_key):
        super().__init__(context="Enable Threads")  # Initialize the SupabaseClient
        self.logger = logging.getLogger("thread_manager")
        self.openai_client = OpenAI(api_key=api_key)  # Renamed to openai_client

        self.api_interaction_handler = APIInteractionHandler(handler_name="Threads")
        

    async def log_thread(self, thread_id: str, assistant_id: str, status: str, assistant_name: str = []):
        thread_data = {
            "thread_id": thread_id,
            "assistant_id": assistant_id,
            "status": status,
            "created_at": get_local_time(),
            "updated_at": get_local_time(),
            "assistant_name": assistant_name
        }
        try:
            response = await asyncio.to_thread(
            lambda: self.client.table('threads').insert(thread_data).execute()  # Corrected to self.client
    
            )
            self.logger.info(f"Thread {status}: {thread_id} logged. Response: {response}")
        except Exception as e:
            self.logger.error(f"Error logging thread {thread_id}: {e}")

    async def create_thread(self, assistant_id: str, assistant_name: str = []):
        start_time = time.time()
        try:
            thread = await asyncio.to_thread(self.openai_client.beta.threads.create)
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)

            await self.log_thread(str(thread.id), str(assistant_id), 'active', assistant_name)
            await self.api_interaction_handler.log_api_interaction(
                endpoint="/start",
                message="Conversation Starting",
                response=f"You have started a conversation with the assistant and thread:{thread}",
                tool_used='Create_Thread',
                response_time_ms=response_time_ms,
                status='success'
            )

            self.logger.info(f"Conversation started with thread ID: {thread.id}")
            return thread
        except Exception as e:
            self.logger.error(f"Error creating thread: {e}")
            raise

    async def update_thread(self, thread_id: str, assistant_id: str):
        start_time = time.time()
        try:
            update_data = {
                "updated_at": get_local_time(),
                "status": "active"
            }

            updated_thread = await asyncio.to_thread(
                lambda: self.client.table('threads').update(update_data).eq('thread_id', thread_id).execute()  # Corrected to self.client
            )

            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)

           
            await self.api_interaction_handler.log_api_interaction(
                endpoint="update_thread",
                message=f"Thread {thread_id} updated",
                response="Update successful",
                tool_used='ThreadManager',
                response_time_ms=response_time_ms,
                status='success'
            )
            return updated_thread
        except Exception as e:
            self.logger.error(f"Error updating thread {thread_id}: {e}")
            raise

    async def delete_thread(self, thread_id: str):
        start_time = time.time()
        try:
            response = await asyncio.to_thread(
                lambda: self.client.table('threads').delete().eq("thread_id", thread_id).execute()  # Corrected to self.client
            )

            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)

            await self.api_interaction_handler.log_api_interaction(
                endpoint="delete_thread",
                message=f"Thread {thread_id} deleted",
                response="Thread deleted successfully",
                tool_used='ThreadManager',
                response_time_ms=response_time_ms,
                status='success'
            )
            return {"detail": "Thread deleted successfully", "response": response}
        except Exception as e:
            self.logger.error(f"Error deleting thread {thread_id}: {e}")
            raise

    async def get_thread(self):
        start_time = time.time()
        try:
            response = await asyncio.to_thread(
                lambda: self.client.table('threads').select('thread_id').execute()
            )
            thread_id= [item['thread_id'] for item in response.data]
    
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
    
            await self.api_interaction_handler.log_api_interaction(
                endpoint="get_thread",
                message="Fetching thread IDs",
                response=f"Thread IDs fetched successfully: {thread_id}",
                tool_used='ThreadManager',
                response_time_ms=response_time_ms,
                status='success'
            )
            return thread_id
        except Exception as e:
            self.logger.error(f"Error fetching thread ID: {e}")
            raise

    async def list_threads(self, start_date: str = None, end_date: str = None, limit: int = 10):
        start_time = time.time()
        try:
            query = self.client.table('threads').select('*')  # Select all columns
    
            # Apply date range filtering
            if start_date:
                start_datetime = datetime.fromisoformat(start_date)
                query = query.filter('updated_at', 'gte', start_datetime)
            if end_date:
                end_datetime = datetime.fromisoformat(end_date)
                query = query.filter('updated_at', 'lte', end_datetime)
    
            # Apply limit and order by updated_at timestamp in descending order
            query = query.order('updated_at', desc=True).limit(limit)
    
            # Execute the query
            response = await asyncio.to_thread(lambda: query.execute())
            threads = response.data
    
            # Extract thread IDs and the last updated_at timestamp
            thread_ids = [item['thread_id'] for item in threads] if threads else []
            last_updated = threads[-1]['updated_at'] if threads else ''
    
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
    
            # Log the API interaction
            await self.api_interaction_handler.log_api_interaction(
                endpoint="list_threads",
                message=f"Listing threads from {start_date} to {end_date}, Limit: {limit}",
                response=f"Threads listed successfully: {thread_ids}",
                tool_used='ThreadManager',
                response_time_ms=response_time_ms,
                status='success'
            )
    
            # Return full thread data
            return threads
    
        except ValueError as ve:
            self.logger.error(f"Error with date format: {ve}")
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            self.logger.error(f"Error listing threads: {e}")
            raise HTTPException(status_code=500, detail=str(e))


    