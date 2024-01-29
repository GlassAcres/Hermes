import openai 
from fastapi import HTTPException
from datetime import datetime
from pytz import timezone
import time
import asyncio
from supabase_handlers.supabase_client import SupabaseClient
from supabase_handlers.thread_handler import ThreadManager
from supabase_handlers.api_interaction_handler import APIInteractionHandler
import logging

def get_local_time():
    local_time = datetime.now(timezone('America/New_York'))
    return local_time.strftime("%Y-%m-%d %H:%M:%S")

class MessageHandler(SupabaseClient):
    def __init__(self, user_id: str, name: str, api_key, thread_handler: ThreadManager, api_interaction_handler: APIInteractionHandler):
        super().__init__(context="Enable Messages")
        self.openai_client = openai.OpenAI(api_key=api_key).beta
        self.logger = logging.getLogger("message_manager")
        self.thread_manager = thread_handler
        self.api_interaction_handler = api_interaction_handler

    async def log_message_action(self, thread_id: str, assistant_id: str, status: str, user_id: str, name: str):
        log_data = {
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
                lambda: self.client.table('api_logs').insert(log_data).execute()
            )
            self.logger.info(f"Message action logged: {response}")
        except Exception as e:
            self.logger.error(f"Error logging message action: {e}")

    async def create_message(self, thread_id: str, role: str, content: str, assistant_id: str, user_id: str, name: str, message_id: str = None):
        try:
            if role not in ["user", "assistant"]:
                raise ValueError("Invalid role: role must be 'user' or 'assistant'.")

            if role == "user":
                message = await asyncio.to_thread(self.openai_client.threads.messages.create, thread_id=thread_id, role=role, content=content)
                message_id = message.id

            if role == "assistant" and not message_id:
                raise ValueError("Message ID must be provided for assistant messages.")

            log_data = {
                "thread_id": thread_id,
                "message_id": message_id,
                "role": role,
                "content": content,
                "assistant_id": assistant_id,
                "user_id": user_id,
                "name": name,
                "created_at": get_local_time()
            }

            await asyncio.to_thread(
                lambda: self.client.table('messages').insert(log_data).execute()
            )
            await self.thread_manager.update_thread(thread_id, assistant_id)

        except Exception as e:
            self.logger.error(f"Error logging message for role {role} in thread {thread_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def retrieve_message(self, thread_id, message_id):
        try:
            message = await self.openai_client.threads.messages.retrieve(thread_id, message_id)
            await self.log_message_action(thread_id, "retrieve", message_id, "success", "Message retrieved successfully")
            return message
        except Exception as e:
            self.logger.error(f"Error retrieving message {message_id} in thread {thread_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def modify_message(self, thread_id, message_id, new_content):
        try:
            updated_message = await self.openai_client.threads.messages.update(thread_id, message_id, content=new_content)
            await self.log_message_action(thread_id, "update", message_id, "success", "Message updated successfully")
            return updated_message
        except Exception as e:
            self.logger.error(f"Error updating message {message_id} in thread {thread_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_message(self, thread_id: str, message_id: str):
        try:
            response = await asyncio.to_thread(
                lambda: self.supabase.table('messages').delete().eq("message_id", message_id).eq("thread_id", thread_id).execute()
            )
            self.logger.info(f"Message {message_id} in thread {thread_id} deleted. Response: {response}")
            await self.log_message_action(thread_id, "delete", message_id, "success", "Message deleted successfully")
        except Exception as e:
            self.logger.error(f"Error deleting message {message_id} in thread {thread_id}: {e}")


    async def list_messages(self, thread_id: str):
        start_time = time.time()
        try:
            query = self.client.table('messages').select('*')
            query = query.filter('thread_id', 'eq', thread_id)
            query = query.order('created_at', desc=False)

            response = await asyncio.to_thread(lambda: query.execute())
            messages = response.data

            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)

            await self.api_interaction_handler.log_api_interaction(
                endpoint="list_messages",
                message=f"Listing messages for thread_id: {thread_id}",
                response=f"Messages listed successfully: {messages}",
                tool_used='MessageHandler',
                response_time_ms=response_time_ms,
                status='success'
            )

            return messages

        except ValueError as ve:
            self.logger.error(f"Value error in list_messages: {ve}")
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            self.logger.error(f"Error listing messages for thread_id {thread_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
