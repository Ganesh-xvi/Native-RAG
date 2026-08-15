from fastapi import Header, HTTPException, Request

from src.utils.config import get_settings


async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    settings = get_settings()
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


def get_app_state(request: Request):
    return request.app.state
