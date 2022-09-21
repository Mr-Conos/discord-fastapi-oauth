import os

import uvicorn
from cachetools import TTLCache
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware

from discord_oauth import DiscordOAuthClient
from discord_oauth.exceptions import DiscordOAuthException, Unauthorized

load_dotenv()

app = FastAPI(
    middleware=[
        Middleware(SessionMiddleware, secret_key=os.getenv("CLIENT_SECRET"))
    ]
)

discord = DiscordOAuthClient(
    client_id=620939694946910218,
    client_secret=os.getenv("CLIENT_SECRET"),
    redirect_uri="http://127.0.0.1:5000/callback",
    scopes=("identify", "guilds"),
    user_cache=TTLCache(maxsize=100, ttl=30)
)


@app.on_event("startup")
async def startup_event():
    await discord.init()


@app.get("/")
async def root(request: Request):
    authorization_url = discord.create_session(request)
    return RedirectResponse(authorization_url)


@app.get("/callback")
async def callback(code: str, state: str, request: Request):
    try:
        await discord.callback(code, state, request)
        return {"success": True}
    except DiscordOAuthException:
        return {"success": False}


@app.get("/home", dependencies=[Depends(DiscordOAuthClient.is_authorized)])
async def home(request: Request):
    user = await discord.fetch_user(request)
    guilds = await discord.fetch_guilds(request)
    return {"user_id": user.id, "username": user.username}


@app.exception_handler(Unauthorized)
async def handle_unauthorized(request: Request, exc):
    return JSONResponse({"message": "unauthorized"}, status_code=401)


if __name__ == "__main__":
    uvicorn.run(app, port=5000, log_level="info")
