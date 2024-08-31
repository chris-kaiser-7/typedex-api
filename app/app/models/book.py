from typing import List
from app.db.base_class import Base
from odmantic import Field

class Book(Base):
    name: str = Field(default="", unique=True)
    instructions: str = Field(default="")
    fields: List[str] = Field()
    field_descriptions: List[str] = Field()
    assistant: str = Field()