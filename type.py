from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import openai
from cache import get_assistant, set_assistant
import os
from main import app
import json

router = APIRouter()

created_assistants = {}

def generate_prompt(type_name, count, properties, ansestry):
    return f'Please create {count} subtypes of {type_name}. Type {type_name} has the properties {properties} and an ansestry of {ansestry}'

model = "gpt-4o"

openai.api_key = os.getenv("OPENAI_API_KEY")

@router.post("/type")
async def generate_type(request: dict):
    #use pydantic instead
    type_name = request.get("type")
    count = request.get("count")

    #use pydantic instead
    if not type_name or not count or not isinstance(count, int) or count <= 0 or count > 10: #use pydandic instead
        raise HTTPException(status_code=400, detail="Invalid request") 

    #use pydantic to type check db obj?
    parent = await app.subtypes_collection.find_one({ "type": type_name })
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")

    book = await app.book_collection.find_one({"name": parent['book'] })

    if book['name'] not in created_assistants:
        new_assistant = openai.beta.assistants.create(
            name=book['name'],
            instructions=book['instructions'],
            model=model
        )
        created_assistants[book['name']] = new_assistant.id
    
    assistant_id = created_assistants[book['name']]

    thread = openai.beta.threads.create()
    parent_properties = parent["properties"]
    ancestry = parent['ancestry'] 
    prompt = generate_prompt(type_name, count, parent_properties, ancestry)

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

            # Save chat to Atlas
            app.types_log_collection.insert_one({
                "assistant_id": assistant_id,
                "thread_id": thread.id,
                "user_message": prompt,
                "assistant_response": response,
                "timestamp": run_status.completed_at 
            })

            #need better parser
            parsed_response = "\n".join(response.split("\n")[1:-1])
            subtypes = json.loads(parsed_response)

            #cap at 10 children (placeholder)
            total_time = 0
            remaining_children = 10 - len(parent.get("children"))
            for subtype in subtypes[:remaining_children]:
                #dynamicly generate pydandic model here?
                if "name" not in subtype:
                    print(f'invalid parse for {subtype}')
                    continue

                # Handle duplicate types
                # Can optimize to have a type book hash table in memory but would have distributed issues
                # This can be better optimized.
                # Perhaps the uniqueness should be ancestry-based instead of based on typename?
                # If this is the case, then it is as simple as checking the parent's children
                # Maybe this could be done in one bulk lookup? 
                # 10 children takes aboue 0.03 seconds of waiting
                empty_check = await app.subtypes_collection.count_documents({ "type": subtype["name"], "book": book["name"] })
                if empty_check != 0:
                    print('duplicate type')
                    continue

                query = { "type": type_name }
                update = {"$push": {"children": subtype["name"]}}
                app.subtypes_collection.update_one(query, update)

                new_ancestry = parent.get("ancestry", [])
                new_ancestry.append(type_name)

                properties = {}
                for field in book['fields']:
                    properties[field] = subtype[field]

                app.subtypes_collection.insert_one({
                    "parent": type_name,
                    "type": subtype["name"],
                    "properties": properties,
                    "ancestry": new_ancestry,
                    "children": [],
                    "book": book['name']
                })

            print(f'total time {total_time}')
            break

    return JSONResponse(content={"subtypes": subtypes}, status_code=200)