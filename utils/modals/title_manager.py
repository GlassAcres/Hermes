from supabase_handlers.message_handler import MessageHandler
from supabase_handlers.thread_handler import ThreadManager
from supabase_handlers.api_interaction_handler import APIInteractionHandler
from openai import OpenAI
import os
import asyncio  # Import asyncio for async operations

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
class TitleMaster:
    def __init__(self, api_key, message_handler: MessageHandler):
        self.message_handler = message_handler
        tool = F"{title_manager}"
        self.client = client.chat.completions.create(
          model="gpt-3.5-turbo",
          messages=[
            {"role": "system", "content": f"{tool}"},
            {"role": "user", "content": "Hello!"}
          ]
        )

    async def generate_thread_title(self, thread_id: str):
        # Retrieve first three messages
        thread_id= thread_id
        client = self.client
        messages = await self.message_handler.list_messages(thread_id)
        if len(messages) > 3:
            messages = messages[:3]

        # Combine messages into a single string
        combined_messages = " ".join([msg['content'] for msg in messages])

        # Generate title using OpenAI API
        prompt = f"Read these messages and suggest a title for the thread: {combined_messages}"
        response = await self.client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[{"role": "system", "content": prompt}]
        )
        title = response.choices[0].message.content.strip()

        # Update thread title in Supabase
        await self.message_handler.thread_manager.update_thread(thread_id, title)

        return title

# Example usage
if __name__ == "__main__":
    api_key = (os.environ['OPEN_API_KEY'])  # Replace with your actual API key
    thread_manager = ThreadManager(api_key)  # Initialize with actual parameters
    api_interaction_handler = APIInteractionHandler(api_key)  # Initialize with actual parameters
    message_handler = MessageHandler(api_key, thread_manager, api_interaction_handler)
    title_manager = TitleMaster(api_key, message_handler)

    # Example thread ID
    thread_id = thread_manager.get_thread_id()
    title = asyncio.run(title_manager.generate_thread_title(thread_id))
    print(f"Generated title: {title}")
