import os
import asyncio
from datetime import datetime
from fastapi import HTTPException
from supabase import create_client, Client


class SupabaseClient:
    def __init__(self):
        self.logger = setup_custom_logger("SupabaseClient")
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        if not supabase_url or not supabase_key:
            self.logger.error("Supabase URL or Key is not set")
            raise ValueError("Supabase URL and Key must be provided")
        self.client = create_client(supabase_url, supabase_key)
        self.logger.info("Supabase Client Initialized")

class UserManager(SupabaseClient):
    def __init__(self):
        super().__init__()

    async def create_user(self, user_data):
        try:
            response = await asyncio.to_thread(
                lambda: self.client.table('users').insert(user_data).execute()
            )
            self.logger.info(f"User created: {response.data}")
            return response.data
        except Exception as e:
            self.logger.error(f"Error creating user: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_user(self, user_id):
        try:
            response = await asyncio.to_thread(
                lambda: self.client.table('users').select("*").eq('user_id', user_id).execute()
            )
            user_data = response.data[0] if response.data else None
            if not user_data:
                raise HTTPException(status_code=404, detail="User not found")
            return user_data
        except Exception as e:
            self.logger.error(f"Error retrieving user: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def update_user(self, user_id, update_data):
        try:
            response = await asyncio.to_thread(
                lambda: self.client.table('users').update(update_data).eq('user_id', user_id).execute()
            )
            self.logger.info(f"User updated: {response.data}")
            return response.data
        except Exception as e:
            self.logger.error(f"Error updating user: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_user(self, user_id):
        try:
            response = await asyncio.to_thread(
                lambda: self.client.table('users').delete().eq('user_id', user_id).execute()
            )
            self.logger.info(f"User deleted: {response.data}")
            return response.data
        except Exception as e:
            self.logger.error(f"Error deleting user: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def list_users(self):
        try:
            response = await asyncio.to_thread(
                lambda: self.client.table('users').select("*").execute()
            )
            return response.data
        except Exception as e:
            self.logger.error(f"Error listing users: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def update_user_customizations(self, user_id, visual_preferences):
        try:
            update_data = {
                "visual_preferences": visual_preferences,
                "updated_at": datetime.utcnow().isoformat()
            }
            response = await asyncio.to_thread(
                lambda: self.client.table('user_customizations').update(update_data).eq('user_id', user_id).execute()
            )
            self.logger.info(f"User customizations updated: {response.data}")
            return response.data
        except Exception as e:
            self.logger.error(f"Error updating user customizations: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# Example usage:
# user_manager = UserManager()
# asyncio.run(user_manager.create_user({...}))
