import asyncio
import json
from openai import OpenAI
from datetime import datetime
from pytz import timezone
from supabase_handlers.supabase_client import SupabaseClient
from supabase_handlers.api_interaction_handler import APIInteractionHandler
import logging

def get_local_time():
    local_time = datetime.now(timezone('America/New_York'))
    return local_time.strftime("%Y-%m-%d %H:%M:%S")

class RunHandler(SupabaseClient):
    def __init__(self, api_key, user_id):
        super().__init__(context="Runs")
        self.logger = logging.getLogger("run_manager")
        self.user_id = user_id
        self.api_interaction_handler = APIInteractionHandler(handler_name="Runs")
        self.openai_client = OpenAI(api_key=api_key)

    async def create_and_log_run(self, thread_id: str, assistant_id: str, model: str, instructions: str, tools_config_files: list):
        # Create run
        tools = [json.load(open(file, 'r')) for file in tools_config_files]
        run = await asyncio.to_thread(
            self.openai_client.beta.threads.runs.create,
            thread_id=thread_id,
            assistant_id=assistant_id,
            model=model,
            instructions=instructions,
            tools=tools
        )
        self.logger.info(f"Run created with ID: {run.id}")

        # Wait for run completion
        while True:
            run_status = await asyncio.to_thread(self.openai_client.beta.threads.runs.retrieve,
                                                 thread_id=thread_id,
                                                 run_id=run.id)
            if run_status.status == 'completed':
                break
            await asyncio.sleep(1)  # Polling interval

        # Log run to Supabase
        await self.log_run(run_status)

    async def log_run(self, run_status):
        run_data = {
            "run_id": run_status.id,
            "created_at": get_local_time(),
            "assistant_id": run_status.assistant_id,
            "thread_id": run_status.thread_id,
            "status": run_status.status,
            "last_error": str(run_status.last_error) if run_status.last_error else None,
            "model": run_status.model,
            "instructions": run_status.instructions,
            "tools": str(run_status.tools),
            "file_ids": str(run_status.file_ids),
            "metadata": str(run_status.metadata),
            "prompt_tokens": run_status.usage.prompt_tokens,
            "completion_tokens": run_status.usage.completion_tokens,
            "total_tokens": run_status.usage.total_tokens
        }
        try:
            response = await asyncio.to_thread(lambda: self.client.table('runs').insert(run_data).execute())
            self.logger.info(f"Run logged. Response: {response}")
        except Exception as e:
            self.logger.error(f"Error logging run: {e}")
