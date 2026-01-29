"""Type definitions for BlockRun XRPL SDK."""

from typing import List, Optional, Literal
from pydantic import BaseModel


class ChatMessage(BaseModel):
    """A single chat message."""
    role: Literal["system", "user", "assistant"]
    content: str


class ChatChoice(BaseModel):
    """A single completion choice."""
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None


class ChatUsage(BaseModel):
    """Token usage information."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatResponse(BaseModel):
    """Response from chat completion."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatChoice]
    usage: Optional[ChatUsage] = None


class Model(BaseModel):
    """Available model information."""
    id: str
    name: str
    provider: str
    description: str
    input_price: float
    output_price: float
    context_window: int
    max_output: int
    available: bool = True


class BlockrunError(Exception):
    """Base exception for BlockRun SDK."""
    pass


class PaymentError(BlockrunError):
    """Payment-related error."""
    pass


class APIError(BlockrunError):
    """API-related error."""
    def __init__(self, message: str, status_code: int, response: Optional[dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response
