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
        super().__init__(context="Enable Threads")
        self.logger = logging.getLogger("thread_manager")
        self.openai_client = OpenAI(api_key=api_key)

        self.api_interaction_handler = APIInteractionHandler(handler_name="Threads")

    async def log_thread(self, thread_id: str, assistant_id: str, status: str, user_id: str, name: str):
        thread_data = {
            "thread_id": thread_id,
            "assistant_id": assistant_id,
            "status": status,
            "user_id": user_id,
            "name": name,
            "created_at": get_local_time(),
            "updated_at": get_local_time()
        }
        try:
            response = await asyncio.to_thread(
                lambda: self.client.table('threads').insert(thread_data).execute()
            )
            self.logger.info(f"Thread {status}: {thread_id} logged. Response: {response}")
        except Exception as e:
            self.logger.error(f"Error logging thread {thread_id}: {e}")

    async def create_thread(self, assistant_id: str, user_id: str, name: str):
        start_time = time.time()
        try:
            thread = await asyncio.to_thread(self.openai_client.beta.threads.create)
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)

            await self.log_thread(str(thread.id), assistant_id, 'active', user_id, name)
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

    async def request_thread(self, thread_id: str, user_id: str):
        start_time = time.time()
        try:
            update_data = {
                "updated_at": get_local_time(),
                "user_id": user_id
            }

            await asyncio.to_thread(
                lambda: self.client.table('threads').update(update_data).eq('thread_id', thread_id).execute()
            )

            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)

            await self.api_interaction_handler.log_api_interaction(
                endpoint="request_thread",
                message=f"User {user_id} requested thread {thread_id}",
                response="Thread requested successfully",
                tool_used='ThreadManager',
                response_time_ms=response_time_ms,
                status='success'
            )
        except Exception as e:
            self.logger.error(f"Error in user requesting thread {thread_id}: {e}")
            raise

    async def update_thread(self, thread_id: str, assistant_id: str):
        start_time = time.time()
        try:
            update_data = {
                "updated_at": get_local_time(),
                "assistant_id": assistant_id
            }

            await asyncio.to_thread(
                lambda: self.client.table('threads').update(update_data).eq('thread_id', thread_id).execute()
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
            return {"detail": "Thread updated successfully"}
        except Exception as e:
            self.logger.error(f"Error updating thread {thread_id}: {e}")
            raise

    async def delete_thread(self, thread_id: str):
        start_time = time.time()
        try:
            response = await asyncio.to_thread(
                lambda: self.client.table('threads').delete().eq("thread_id", thread_id).execute()
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

    async def get_thread(self, thread_id: str):
        start_time = time.time()
        try:
            response = await asyncio.to_thread(
                lambda: self.client.table('threads').select('*').eq('thread_id', thread_id).execute()
            )

            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)

            if not response.data:
                raise ValueError("Thread not found")

            await self.api_interaction_handler.log_api_interaction(
                endpoint="get_thread",
                message=f"Fetching thread {thread_id}",
                response=f"Thread fetched successfully: {response.data[0]}",
                tool_used='ThreadManager',
                response_time_ms=response_time_ms,
                status='success'
            )
            return response.data[0]
        except Exception as e:
            self.logger.error(f"Error fetching thread {thread_id}: {e}")
            raise

    async def list_threads(self, start_date: str = None, end_date: str = None, limit: int = 10):
        start_time = time.time()
        try:
            query = self.client.table('threads').select('*')

            if start_date:
                start_datetime = datetime.fromisoformat(start_date)
                query = query.filter('updated_at', 'gte', start_datetime)
            if end_date:
                end_datetime = datetime.fromisoformat(end_date)
                query = query.filter('updated_at', 'lte', end_datetime)

            query = query.order('updated_at', desc=True).limit(limit)

            response = await asyncio.to_thread(lambda: query.execute())
            threads = response.data

            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)

            await self.api_interaction_handler.log_api_interaction(
                endpoint="list_threads",
                message=f"Listing threads from {start_date} to {end_date}, Limit: {limit}",
                response=f"Threads listed successfully",
                tool_used='ThreadManager',
                response_time_ms=response_time_ms,
                status='success'
            )
            return threads
        except Exception as e:
            self.logger.error(f"Error listing threads: {e}")
            raise
