from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str
    content: str
    
    model_config = {"extra": "ignore"}

class ChatCompletionRequest(BaseModel):
    model: str = "gpt-3.5-turbo"
    messages: List[ChatMessage]
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0
    frequency_penalty: Optional[float] = 0
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None

class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None
    
    model_config = {"extra": "ignore"}

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionResponseChoice]
    usage: Optional[Dict[str, Any]] = None
    
    model_config = {"extra": "ignore"}
