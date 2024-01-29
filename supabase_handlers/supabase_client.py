from supabase import create_client, Client
from utils.logger import setup_custom_logger
import os


class SupabaseClient:
    def __init__(self, context="Initialize"):
        self.logger = setup_custom_logger(__name__)
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            self.logger.error("Supabase URL or Key is not set")
            raise ValueError("Supabase URL and Key must be provided")

        try:
            self.client = create_client(supabase_url, supabase_key)
            self.logger.info(f"{context} -> Success")
        except Exception as e:
            self.logger.error(f"Error initializing Supabase client in {context}: {e}", exc_info=True)
            raise
