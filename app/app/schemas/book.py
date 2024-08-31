from typing import List
from typing_extensions import Self
from pydantic import BaseModel, model_validator

# Define a Pydantic model for the book
class BookCreate(BaseModel):
    name: str
    fields: List[str] #need to add validation that can't have spaces
    field_descriptions: List[str] 
    assistant: str

    @model_validator(mode='after')
    def validate_fields_and_descriptions(self) -> Self:
        if len(self.fields) != len(self.field_descriptions):
            raise ValueError("fields and field_descriptions must have the same length")
        return self

class BookUpdate(BookCreate):
    pass