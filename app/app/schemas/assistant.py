from typing import List
from typing_extensions import Self
from pydantic import BaseModel, model_validator

class AssistantCreate(BaseModel):
    name: str
    template: str

class AssistantUpdate(BaseModel):
    template: str