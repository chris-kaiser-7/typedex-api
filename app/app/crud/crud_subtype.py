import logging
import openai
import json
from string import Template
from motor.core import AgnosticDatabase
from asyncio import gather

from app.crud.base import CRUDBase
from app.models import Subtype
from app.schemas import SubtypeCreate, SubtypeUpdate, SubtypeGenerate
from app.core.config import settings
from .crud_book import book as crud_book

def generate_prompt(type_name, count, properties, ansestry):
    return f'Please create {count} subtypes of {type_name}. Type {type_name} has the properties {properties} and an ansestry of {ansestry}'

class CRUDSubtype(CRUDBase[Subtype, SubtypeCreate, SubtypeUpdate]):
    def __init__(self, model):
        super().__init__(model)
        self.created_assistants = {}

    async def get_by_name_and_book(self, *, name: str, book: str) -> Subtype | None:
        return await self.engine.find_one(Subtype, Subtype.name == name, Subtype.book == book)
    
    #TODO: need get by book

    async def generate_children(self, *, db: AgnosticDatabase, obj_in: SubtypeGenerate) -> list[Subtype]:
        book = crud_book.get_by_name(name=obj_in.book)
        parent = self.get_by_name_and_book(name=obj_in.parent, book=obj_in.book)

        book, parent = await gather(book, parent)

        if not book or not parent:
            return []
        if book.name not in self.created_assistants:
            new_assistant = openai.beta.assistants.create(
                name=book.name,
                instructions=book.instructions,
                model=settings.OPENAI_MODEL
            )
            self.created_assistants[book.name] = new_assistant.id

        assistant_id = self.created_assistants[book.name]

        thread = openai.beta.threads.create()
        prompt = generate_prompt(obj_in.parent, obj_in.count, parent.properties, parent.ancestry)

        openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt
        )
        run = openai.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )

        while True:
            run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            # need to have fail safe or timeout status "completed" not returned
            if run_status.status == "completed":
                messages = openai.beta.threads.messages.list(thread_id=thread.id)
                response = next(msg for msg in messages.data if msg.role == "assistant").content[0].text.value

                logging.info({
                    "assistant_id": assistant_id,
                    "thread_id": thread.id,
                    "user_message": prompt,
                    "assistant_response": response,
                    "timestamp": run_status.completed_at 
                })

                #TODO: need better parser
                parsed_response = "\n".join(response.split("\n")[1:-1])

                # logging.info(parsed_response)

                subtypes = json.loads(parsed_response) #TODO: somehow integrate a dynamic pydantic model here based on book fileds

                #cap at 10 children (placeholder)
                remaining_children = 10 - len(parent.children)
                db_subtypes = []
                db_tasks = []
                for subtype in subtypes[:remaining_children]:
                    #dynamicly generate pydandic model here?
                    if "name" not in subtype:
                        logging.info(f'invalid parse for {subtype}')
                        continue

                    # Handle duplicate types
                    # Can optimize to have a type book hash table in memory but would have distributed issues
                    # This can be better optimized.
                    # Perhaps the uniqueness should be ancestry-based instead of based on typename?
                    # If this is the case, then it is as simple as checking the parent's children
                    # Maybe this could be done in one bulk lookup? 
                    # 10 children takes about 0.03 seconds of waiting
                    empty_check = await self.engine.count(Subtype, Subtype.name == subtype["name"], Subtype.book == book.name)
                    if empty_check != 0:
                        logging.info('duplicate type')
                        continue

                    #TODO: see if it is possable to do $push in odmantic engine and not lose performance. also consider doing a bulk patch
                    query = { "name": obj_in.parent }
                    update = {"$push": {"children": subtype["name"]}}
                    update_task = await db["subtype"].update_one(query, update)

                    new_ancestry = [*parent.ancestry, obj_in.parent] 

                    properties = {}
                    for field in book.fields:
                        properties[field] = subtype[field]

                    db_subtype = Subtype(
                        name=subtype["name"],
                        parent=obj_in.parent,
                        book=book.name,
                        properties=properties,
                        ancestry=new_ancestry,
                        children=[],
                    )
                    db_task = self.engine.save(db_subtype)
                    # db_subtypes.append(db_subtype)
                    db_tasks.append(db_task)

                completed_tasks = await gather(*db_tasks)
                db_subtypes.extend(completed_tasks)
                break
        logging.info(db_subtypes)
        logging.info(type(db_subtypes))
        return db_subtypes



subtype = CRUDSubtype(Subtype)