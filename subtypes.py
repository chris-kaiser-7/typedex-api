from main import app
from fastapi import APIRouter
from typing import List
from bson import ObjectId
from fastapi import HTTPException

router = APIRouter()

@router.get("/subtypes/")
async def get_all_subtypes():
    subtypes = app.subtypes_collection.find()
    subtypes_list = []
    async for subtype in subtypes:
        subtype["_id"] = str(subtype["_id"])
        subtypes_list.append(subtype)
    return subtypes_list

@router.get("/subtypes/{subtype_type}")
async def get_subtype_by_type(subtype_type: str):
    subtype = await app.subtypes_collection.find_one({"type": subtype_type})
    if subtype:
        subtype["_id"] = str(subtype["_id"])
    return subtype

@router.get("/subtypes/children/{subtype_type}")
async def get_subtype_children(subtype_type: str):
    subtype = await app.subtypes_collection.find_one({"type": subtype_type})
    if subtype:
        subtype["_id"] = str(subtype["_id"])
    return subtype["children"]

@router.get("/subtypes/children/")
async def get_all_subtype_children():
    subtypes = app.subtypes_collection.find()
    children = []
    async for subtype in subtypes:
        subtype["_id"] = str(subtype["_id"])
        children.extend(subtype["children"])
    return children

from pydantic import BaseModel

class Subtype(BaseModel):
    general_description: str
    physical_description: str
    type: str

@router.post("/subtypes/")
async def create_subtype(subtype: Subtype):
    existing_subtype = await app.subtypes_collection.find_one({"type": subtype.type})
    if existing_subtype:
        raise HTTPException(status_code=400, detail="Subtype with this type already exists")
    subtype_dict = subtype.dict()
    subtype_dict["children"] = []
    result = await app.subtypes_collection.insert_one(subtype_dict)
    if not result.acknowledged:
        raise HTTPException(status_code=500, detail="Failed to create subtype")
    return subtype_dict