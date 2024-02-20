# tool_config_manager.py

import json
import os

class ToolConfigManager:
    def __init__(self):
        self.loaded_tools = {}

    def load_tool_config(self, tool_name):
        try:
            file_path = f'./utils/tools/{tool_name}_config.json'
            with open(file_path, 'r') as file:
                config = json.load(file)
            # Add more validation logic if needed
            return config
        except Exception as e:
            print(f"Error loading tool {tool_name}: {e}")
            return None

    def initialize_tools(self):
        tools = ["bsp_search", "trade_leads_search", "consolidated_screening_list_search", "custom_google_search"]

        for tool in tools:
            config = self.load_tool_config(tool)
            if config:
                print(f"Tool: {tool} loaded successfully.")
                self.loaded_tools[tool] = config
            else:
                print(f"Failed to load tool: {tool}")

    def get_tools(self):
        return self.loaded_tools
