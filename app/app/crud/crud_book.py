from app.crud.base import CRUDBase
from app.models import Book
from app.schemas import BookCreate
from string import Template

class CRUDBook(CRUDBase[Book, BookCreate, BookCreate]):
    async def get_by_name(self, *, name: str) -> Book | None:
        return await self.engine.find_one(Book, Book.name == name)

    async def create_from_template(self, *, obj_in: BookCreate, template: str) -> Book | None: # noqa
        #should instuction creation be moved?
        fields_obj = {'fields': obj_in.fields, 'field_descriptions': obj_in.field_descriptions}
        instructions = Template(template).substitute(fields_obj) + '\n'
        #TODO: update this to be cleaner by using json to string on the zip or something.
        instructions += f'```json\n[{{"name":"the name",'
        for field, descriptions in zip(obj_in.fields, obj_in.field_descriptions):
            instructions += f'"{field}": "{descriptions}",'
        instructions = instructions[:-1]
        instructions += '}]\n```'

        book = {
            **obj_in.model_dump(),
            "instructions": instructions
        }
        return await self.engine.save(Book(**book))

book : CRUDBook = CRUDBook(Book)