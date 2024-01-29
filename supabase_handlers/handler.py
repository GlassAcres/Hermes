from datetime import datetime
from supabase_py import create_client, Client
from typing import List
from utils.logger import setup_custom_logger 
from pytz import timezone
import asyncio

class SupabaseHandler:
    def __init__(self, supabase_url: str, supabase_key: str):
        self.logger = setup_custom_logger(__name__)
        try:
           self.logger.info("[STATUS] Supabase Handler Initialized")
        except Exception as e:
            self.logger.error(f"Error initializing Supabase client: {e}", exc_info=True)

    async def log_api_interaction(self, thread_id: str, message: str, response: str, tool_used: str, response_time_ms: int, status: str):
        log_data = {
            "thread_id": thread_id,
            "request_timestamp": datetime.now(timezone("America/New_York")),
            "message": message,
            "response": response,
            "tool_used": tool_used,
            "response_time_ms": response_time_ms,
            "status": status
        }
        try:
            response = await asyncio.to_thread(
                self.supabase.table('api_logs').insert(log_data).execute
            )
            self.logger.info(f"API log inserted: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error inserting API log: {e}", exc_info=True)

    async def log_thread_creation(self, thread_id: str, assistant_id: str):
        thread_data = {
            "thread_id": thread_id,
            "assistant_id": assistant_id,
            "created_at": datetime.now().isoformat()
        }
        try:
            response = await asyncio.to_thread(
                self.supabase.table('threads').insert(thread_data).execute
            )
            self.logger.info(f"Thread log inserted: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error logging thread creation: {e}", exc_info=True)

   
    async def insert_message_log(self, thread_id: str, sender: str, message: str, assistant_id: str):
        message_data = {
            "thread_id": thread_id,
            "sender": sender,
            "message": message,
            "assistant_id": assistant_id,
            "timestamp": datetime.now().isoformat()
        }
        try:
            response = await self.supabase.table('messages').insert(message_data).execute()
            self.logger.info(f"Message log inserted: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error inserting message log: {e}", exc_info=True)

    async def fetch_thread_messages(self, thread_id: str) -> List[dict]:
        try:
            data, error = await self.supabase.table('message_logs').select('*').eq('thread_id', thread_id).order('timestamp', ascending=True).execute()
            if error:
                self.logger.error(f"Error fetching thread messages: {error}", exc_info=True)
                return []
            self.logger.info(f"Messages fetched for thread {thread_id}: {data}")
            return data
        except Exception as e:
            self.logger.error(f"Exception fetching thread messages: {e}", exc_info=True)
            return []
