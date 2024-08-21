from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.openapi.models import SecurityScheme as SecuritySchemeModel
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel, OAuthFlowPassword
import os
from dotenv import load_dotenv

load_dotenv() # only needed for dev

@asynccontextmanager
async def db_lifespan(app: FastAPI):
    # Load the ML model
    app.mongodb_client = AsyncIOMotorClient(os.getenv("ATLAS_URI"))
    app.database = app.mongodb_client["typedex"]
    
    ping_response = await app.database.command("ping")
    if int(ping_response["ok"]) != 1:
        raise Exception("Problem connecting to database cluster.")
    else:
        print("Connected to database cluster.") #use logging instead

    app.assistant_collection = app.database["assistants"]
    app.types_log_collection = app.database["types_log"]
    app.subtypes_collection = app.database["subtypes"]
    app.user_collection = app.database["users"]
    app.book_collection = app.database["books"]
    
    yield
    app.mongodb_client.close()
    print("shutdown")

app = FastAPI(
    lifespan=db_lifespan,
    # openapi_components={
    #     "securitySchemes": {
    #         "OAuth2PasswordBearer": SecuritySchemeModel(
    #             type="oauth2",
    #             flows=OAuthFlowsModel(
    #                 password=OAuthFlowPassword(tokenUrl="token")
    #             ),
    #         )
    #     }
    # },
    # openapi={"security": [{"OAuth2PasswordBearer": []}]},
)

#TODO: allow more appropriate CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
) 

# from routers.type import router as type_router
# from routers.subtypes import router as subtype_router
# from routers.auth import router as auth_router
# from routers.book import router as book_router
# from routers.assistant import router as assistant_router

from .routers import assistant, auth, book, subtypes, type  
app.include_router(type.router, prefix="/api/v1")
app.include_router(subtypes.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(book.router, prefix="/api/v1")
app.include_router(assistant.router, prefix="/api/v1")
