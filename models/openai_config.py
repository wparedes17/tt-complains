from dotenv import dotenv_values
from dataclasses import dataclass
from pydantic import BaseModel
from typing_extensions import TypeVar

config = dotenv_values("openai.env")

T = TypeVar('T', bound=BaseModel)

@dataclass(frozen=True)
class OpenAIConfig:
    api_key = config.get('LLM_API_KEY')
    organization = config.get('LLM_ORGANIZATION')
    project = config.get('LLM_PROJECT')
    model = config.get('LLM_MODEL')
    temperature = config.get('LLM_TEMPERATURE', 0.7)
    max_tokens = config.get('LLM_MAX_TOKENS', 2048)