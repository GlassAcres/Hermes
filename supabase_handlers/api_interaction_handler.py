from datetime import datetime
import asyncio
from supabase_handlers.supabase_client import SupabaseClient

from pytz import timezone

def get_local_time():
    local_time = datetime.now(timezone('America/New_York'))
    return local_time.strftime("%Y-%m-%d %H:%M:%S")

class APIInteractionHandler(SupabaseClient):
    def __init__(self, handler_name):
        # Ensure parent constructor is called
        super().__init__(context=f"{handler_name} Logging")
   
        

    async def log_api_interaction(self, endpoint: str, message: str,
                                  response: str, tool_used: str,
                                  response_time_ms: int, status: str):
        log_data = {
            "endpoint": endpoint,
            "request_timestamp": get_local_time(),
            "message": message,
            "response": response,
            "tool_used": tool_used,
            "response_time_ms": response_time_ms,
            "status": status
        }
        try:
            # Correctly call the execute method as a function
            response = await asyncio.to_thread(
                lambda: self.client.table('api_logs').insert(log_data).execute()
            )
            self.logger.info(f"API log inserted: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error inserting API log: {e}", exc_info=True)
