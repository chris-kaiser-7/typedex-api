from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from cache import init_cache
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.openapi.models import SecurityScheme as SecuritySchemeModel
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel, OAuthFlowPassword
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    app.mongodb_client = AsyncIOMotorClient(os.getenv("ATLAS_URI"))
    app.database = app.mongodb_client["typedex"]
    
    ping_response = await app.database.command("ping")
    if int(ping_response["ok"]) != 1:
        raise Exception("Problem connecting to database cluster.")
    else:
        print("Connected to database cluster.")

    app.assistant_collection = app.database["assistants"]
    app.types_log_collection = app.database["types_log"]
    app.subtypes_collection = app.database["subtypes"]
    app.user_collection = app.database["users"]
    
    yield
    app.mongodb_client.close()
    print("shutdown")

app = FastAPI(
    lifespan=lifespan,
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from type import router as type_router
from subtypes import router as subtype_router
from auth import router as auth_router
app.include_router(type_router, prefix="/api/v1")
app.include_router(subtype_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
