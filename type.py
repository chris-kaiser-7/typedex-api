from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import openai
from cache import get_assistant, set_assistant
import os
from main import app
import json

router = APIRouter()

created_assistants = {}

def generate_prompt(subtype, count, general_desc, ansestry):
    return f'Please create {count} subtypes of {subtype}. Type {subtype} has a general descirpiton of {general_desc} and an ansestry of {ansestry}'
model = "gpt-4o"


@router.post("/type")
async def generate_type(request: dict):
    type_name = request.get("type")
    assistant_name = request.get("assistant")
    count = request.get("count")

    if not type_name or not assistant_name or not count or not isinstance(count, int) or count <= 0 or count > 10:
        raise HTTPException(status_code=400, detail="Invalid request")

    assistant_data = await get_assistant(assistant_name)
    if not assistant_data:
        assistant_data = await app.assistant_collection.find_one({"name": assistant_name})
        if not assistant_data:
            raise HTTPException(status_code=404, detail="Assistant not found")
        await set_assistant(assistant_name, assistant_data)

    openai.api_key = os.getenv("OPENAI_API_KEY")

    if assistant_name not in created_assistants:
        new_assistant = openai.beta.assistants.create(
            name=assistant_name,
            instructions=assistant_data.get("instructions"),
            model=model
        )

        created_assistants[assistant_name] = new_assistant.id
    
    assistant_id = created_assistants[assistant_name]

    thread = openai.beta.threads.create()
    
    parent = await app.subtypes_collection.find_one({ "type": type_name })
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")
    general_desc = parent["general_description"] 
    ancestry = parent['ancestry'] 
    prompt = generate_prompt(type_name, count, general_desc, ancestry)

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
        if run_status.status == "completed":
            messages = openai.beta.threads.messages.list(thread_id=thread.id)
            response = next(msg for msg in messages.data if msg.role == "assistant").content[0].text.value

            # Save chat to Atlas
            app.types_log_collection.insert_one({
                "assistant_id": assistant_id,
                "thread_id": thread.id,
                "user_message": prompt,
                "assistant_response": response,
                "timestamp": run_status.completed_at  # Or use another timestamp field
            })

            #better parser
            parsed_response = "\n".join(response.split("\n")[1:-1])
            subtypes = json.loads(parsed_response)

            for subtype in subtypes:
                if "name" not in subtype or "general_description" not in subtype or "physical_description" not in subtype:
                    print("invalid parse")
                    continue

                #handle duplicate types since its not unique 
                empty_check = await app.subtypes_collection.count_documents({ "type": subtype["name"] })
                if empty_check != 0:
                    print('duplicate type')
                    continue

                # Check if the parent already has 10 children
                parent = await app.subtypes_collection.find_one({ "type": type_name })
                if parent and len(parent.get("children", [])) >= 10:
                    raise HTTPException(status_code=400, detail="Parent already has 10 children")

                # Check if the parent type exists
                parent_type = await app.subtypes_collection.find_one({ "type": type_name })

                if parent_type:
                    # If it exists, update its children
                    query = { "type": type_name }
                    update = {"$push": {"children": subtype["name"]}}
                    app.subtypes_collection.update_one(query, update)
                else:
                    # If it doesn't exist, create a new document for the parent type
                    parent_type = {
                        "type": type_name,
                        "children": [subtype["name"]],
                        "ancestry": []
                    }
                    app.subtypes_collection.insert_one(parent_type)

                new_ancestry = parent_type.get("ancestry", [])
                new_ancestry.append(type_name)

                app.subtypes_collection.insert_one({
                    "parent_type": type_name,
                    "type": subtype["name"],
                    "general_description": subtype["general_description"],
                    "physical_description": subtype["physical_description"],
                    "ancestry": new_ancestry,
                    "children": []
                })

            break

    return JSONResponse(content={"subtypes": subtypes}, status_code=200)