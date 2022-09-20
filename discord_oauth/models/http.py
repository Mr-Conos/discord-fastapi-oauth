from typing import TypedDict, Literal


class AccessTokenExchangePayload(TypedDict):
    client_id: int
    client_secret: str
    grant_type: Literal["authorization_code"]
    code: str
    redirect_uri: str


class AccessTokenResponse(TypedDict):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
    scope: str
