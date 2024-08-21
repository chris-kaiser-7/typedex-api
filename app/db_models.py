from pydantic import BaseModel
from typing import List

class Book(BaseModel):
    name: str
    instructions: str
    fields: List[str]
    field_descriptions: List[str]
    assistant: str

class Subtype(BaseModel):
    parent: str | None = None 
    type: str
    properties: dict[str, str | List[str]] #should this be a list of tuples? 
    ancestry: List[str]
    children: List[str]
    book: str

class Assistant(BaseModel):
    name: str
    template: str