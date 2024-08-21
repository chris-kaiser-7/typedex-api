import secrets
from typing import Any, Dict, List, Union, Annotated

from pydantic import AnyHttpUrl, EmailStr, HttpUrl, field_validator, BeforeValidator
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings

def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)

    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyHttpUrl] | str, BeforeValidator(parse_cors)
    ] = []

    PROJECT_NAME: str
    MONGO_DATABASE_URI: str
    OPENAI_API_KEY: str

settings = Settings()
