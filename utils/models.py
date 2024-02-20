
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class Tool(BaseModel):
    type: str  # e.g., "code_interpreter" or "retrieval"

class AssistantRequest(BaseModel):
    model: str
    user_id: str
    instructions: Optional[str] = None
    name: Optional[str] = None
    file_ids: Optional[List[str]] = []
    tools: Optional[List[Tool]] = []


class AssistantUpdateRequest(BaseModel):
    model: str
    user_id: str
    instructions: Optional[str] = None
    name: Optional[str] = None
    file_ids: Optional[List[str]] = []
    tools: Optional[List[Tool]] = []
    
class ThreadCreateRequest(BaseModel):
    messages: List[Dict[str, str]]
    metadata: Optional[dict] = None
    assistant: Optional[str] = None 
    user_id: Optional[str] = None
class ThreadUpdateRequest(BaseModel):
    metadata: Optional[dict] = None
    assistant: Optional[str] = None 
    user_id: Optional[str] = None
    

class ChatRequest(BaseModel):
    thread_id: str
    message: str
    name: Optional[str] = None
    instructions: Optional[str] = None
    model: Optional[str] = None
    tools: Optional[List[dict]] = None
    file_ids: Optional[List[str]] = None
    user_id: Optional[str] = None


class ThreadModel(BaseModel):
    thread_id: str
    name: Optional[str]
    assistant_id: Optional[str]
    status: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    user_id: Optional[str]

class MessageModel(BaseModel):
    message_id: str
    thread_id: str
    content: str
    role: str
    created_at: Optional[datetime]
    assistant_id: str
    user_id: str
    name: Optional[str]
class MessageCreateRequest(BaseModel):
    thread_id: str = Field(..., description="The ID of the thread to create a message for.")
    role: str = Field(..., description="The role of the entity that is creating the message. Currently only user is supported.")
    content: str = Field(..., description="The content of the message.")
    file_ids: Optional[List[str]] = Field(default_factory=list, description="A list of File IDs that the message should use. Maximum of 10 files.")
    metadata: Optional[dict] = Field(default=None, description="Set of 16 key-value pairs for additional structured information.")

class MessageUpdateRequest(BaseModel):
    new_content: Optional[str] = Field(None, description="The new content of the message.")
    metadata: Optional[dict] = Field(default=None, description="Set of 16 key-value pairs for additional structured information.")
