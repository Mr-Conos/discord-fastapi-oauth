import json
from random import SystemRandom
from typing import Tuple, Dict, List

import aiohttp
import jwt
from cachetools import Cache, LRUCache
from fastapi import Request

from . import exceptions, constants as const
from .models.discord import User, Guild
from .models.http import AccessTokenExchangePayload, AccessTokenResponse


class DiscordOAuthClient:
    """Client for Discord OAuth2."""

    def __init__(
            self,
            client_id: int,
            client_secret: str,
            redirect_uri: str,
            scopes: Tuple[str, ...],
            user_cache: Cache = None,
            prompt: str = "consent"
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes
        self.prompt = prompt

        self.client_session: aiohttp.ClientSession = None  # type: ignore

        self.user_cache = user_cache if user_cache else LRUCache(maxsize=100)

    async def _request(self, method: str, url: str, data: Dict = None, auth: Request = None) -> Dict:
        headers = {}
        if auth:
            headers["Authorization"] = f"Bearer {auth.session['DISCORD_ACCESS_TOKEN']}"

        async with self.client_session.request(method, url, headers=headers, data=data) as resp:
            if resp.status == 401:
                raise exceptions.Unauthorized()
            elif resp.status == 403:
                raise exceptions.AccessDenied()
            elif resp.status == 429:
                raise exceptions.RateLimited(await resp.json(), resp.headers)

            try:
                return await resp.json()
            except json.JSONDecodeError as e:
                raise e

    async def init(self) -> None:
        self.client_session = aiohttp.ClientSession()

    def create_session(self, request: Request) -> str:
        rand = SystemRandom()
        decoded_state = "".join(rand.choice(const.UNICODE_ASCII_CHARACTER_SET) for _ in range(30))
        decoded_state_data = {"state_secret": decoded_state}
        encoded_state = jwt.encode(decoded_state_data, self.client_secret, algorithm="HS256")

        request.session["DISCORD_OAUTH2_STATE"] = encoded_state

        response_type = "response_type=code"
        client_id = f"client_id={self.client_id}"
        scope = f"scope={'%20'.join(scope for scope in self.scopes)}"
        state = f"&state={encoded_state}"
        redirect_uri = f"redirect_uri={self.redirect_uri}"
        prompt = f"prompt={self.prompt}"

        return f"{const.DISCORD_BASE_AUTH_URL}?{response_type}&{client_id}&{scope}&{state}&{redirect_uri}&{prompt}"

    async def callback(self, code: str, state: str, request: Request):
        decoded_received_state = jwt.decode(state, self.client_secret, algorithms="HS256")
        decoded_stored_state = jwt.decode(
            request.session["DISCORD_OAUTH2_STATE"], self.client_secret, algorithms=["HS256"]
        )

        if decoded_received_state != decoded_stored_state:
            return False

        payload: AccessTokenExchangePayload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri
        }

        data: AccessTokenResponse = await self._request("post", const.DISCORD_TOKEN_URL, payload)

        del request.session["DISCORD_OAUTH2_STATE"]
        request.session["DISCORD_ACCESS_TOKEN"] = data["access_token"]

    async def fetch_user(self, request: Request) -> User:
        if "DISCORD_USER_ID" in request.session:
            try:
                return self.user_cache[request.session["DISCORD_USER_ID"]]
            except KeyError:
                pass

        try:
            data = await self._request("get", const.DISCORD_USER_BASE_URL, auth=request)
            user = User(data)
            request.session["DISCORD_USER_ID"] = user.id
            self.user_cache[user.id] = user
            return user
        except exceptions.RateLimited as e:
            if "DISCORD_USER_ID" in request.session:
                return await self.fetch_user(request)

            raise e

    async def fetch_guilds(self, request: Request) -> List[Guild]:
        if "DISCORD_USER_ID" in request.session:
            try:
                user = self.user_cache[request.session["DISCORD_USER_ID"]]
                if user and user.guilds:
                    return user.guilds

                if not user:
                    await self.fetch_user(request)
            except KeyError:
                pass
        else:
            await self.fetch_user(request)

        try:
            data = await self._request("get", const.DISCORD_USER_GUILDS_URL, auth=request)
            guilds = {int(guild_data["id"]): Guild(guild_data) for guild_data in data}
            self.user_cache[request.session["DISCORD_USER_ID"]].guilds = guilds
            return list(guilds.values())
        except exceptions.RateLimited as e:
            guilds = self.user_cache[request.session["DISCORD_USER_ID"]].guilds
            if guilds:
                return guilds

            raise e

    @staticmethod
    def is_authorized(request: Request):
        if "DISCORD_ACCESS_TOKEN" not in request.session:
            raise exceptions.Unauthorized
