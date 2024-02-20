import logging
import time
from datetime import datetime
from pytz import timezone
import asyncio
from fastapi import HTTPException
from supabase_handlers.supabase_client import SupabaseClient
from supabase_handlers.api_interaction_handler import APIInteractionHandler

def get_local_time():
    local_time = datetime.now(timezone('America/New_York'))
    return local_time.strftime("%Y-%m-%d %H:%M:%S")

class AssistantManager(SupabaseClient):

    def __init__(self):
        super().__init__(context="Assistants")  # Initialize SupabaseClient
        self.logger = logging.getLogger("assistant_manager")
        self.api_interaction_handler = APIInteractionHandler(handler_name="Assistants")

    async def log_assistant(self, assistant_id: str, name: str, model: str, instructions: str, file_ids: str):
        assistant_data = {
            "assistant_id": assistant_id,
            "name": name,
            "model": model,
            "instructions": instructions,
            "file_ids": file_ids,
            "created_at": get_local_time(),
            "updated_at": get_local_time()
        }
        try:
            response = await asyncio.to_thread(lambda: self.client.table('assistants').insert(assistant_data).execute())
            self.logger.info(f"Assistant logged. Response: {response}")
        except Exception as e:
            self.logger.error(f"Error logging assistant: {e}")

    async def create_assistant(self, model, instructions=None, name=None, file_ids=None):
        try:
            assistant_data = {
                "name": name,
                "model": model,
                "instructions": instructions,
                "file_ids": file_ids,
                "created_at": get_local_time(),
                "updated_at": get_local_time()
            }
            response = await asyncio.to_thread(lambda: self.client.table('assistants').insert(assistant_data).execute())
            self.logger.info(f"Assistant created. Response: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error creating assistant: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def update_assistant(self, assistant_id, model, instructions=None, name=None, file_ids=None):
        try:
            db_update_data = {
                "updated_at": datetime.now(timezone("America/New_York")).isoformat(),
                "name": name,
                "model": model,
                "instructions": instructions,
                "file_ids": file_ids
            }
            response = await asyncio.to_thread(lambda: self.client.table('assistants').update(db_update_data).eq('assistant_id', assistant_id).execute())
            self.logger.info(f"Assistant updated. Response: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error updating assistant: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_assistant(self, assistant_id):
        try:
            response = await asyncio.to_thread(lambda: self.client.table('assistants').delete().eq('assistant_id', assistant_id).execute())
            self.logger.info(f"Assistant deleted. Response: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error deleting assistant: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_assistant(self, assistant_id):
        try:
            response = await asyncio.to_thread(lambda: self.client.table('assistants').select('*').eq('assistant_id', assistant_id).execute())
            if not response.data:
                raise HTTPException(status_code=404, detail="Assistant not found")
            return response.data[0]
        except Exception as e:
            self.logger.error(f"Error fetching assistant: {e}")
            raise

    async def list_assistants(self, start_date: str = None, end_date: str = None, limit: int = 10):
        try:
            query = self.client.table('assistants').select('*')

            if start_date:
                start_datetime = datetime.fromisoformat(start_date)
                query = query.filter('updated_at', 'gte', start_datetime)
            if end_date:
                end_datetime = datetime.fromisoformat(end_date)
                query = query.filter('updated_at', 'lte', end_datetime)

            query = query.order('updated_at', desc=True).limit(limit)
            response = await asyncio.to_thread(lambda: query.execute())
            return response.data
        except ValueError as ve:
            self.logger.error(f"Error with date format: {ve}")
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            self.logger.error(f"Error listing assistants: {e}")
            raise HTTPException(status_code=500, detail=str(e))
